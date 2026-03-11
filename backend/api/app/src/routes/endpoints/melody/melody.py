import asyncio
import base64
import logging
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.src.services.melody_generator import generate_melody as generate_melody_service
from app.src.services.melody_generator import generate_melody_streaming
from app.src.services.midi_service import convert_midi_to_wav, create_midi_from_tokens

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

router = APIRouter()

# Curated list of General MIDI instruments that work well with the generated melodies
INSTRUMENTS = [
    {"id": 0, "name": "Acoustic Grand Piano"},
    {"id": 1, "name": "Bright Acoustic Piano"},
    {"id": 2, "name": "Electric Grand Piano"},
    {"id": 4, "name": "Electric Piano 1"},
    {"id": 5, "name": "Electric Piano 2"},
    {"id": 6, "name": "Harpsichord"},
    {"id": 7, "name": "Clavinet"},
    {"id": 8, "name": "Celesta"},
    {"id": 10, "name": "Music Box"},
    {"id": 11, "name": "Vibraphone"},
    {"id": 12, "name": "Marimba"},
    {"id": 13, "name": "Xylophone"},
    {"id": 16, "name": "Drawbar Organ"},
    {"id": 19, "name": "Church Organ"},
    {"id": 24, "name": "Acoustic Guitar (Nylon)"},
    {"id": 25, "name": "Acoustic Guitar (Steel)"},
    {"id": 26, "name": "Electric Guitar (Jazz)"},
    {"id": 40, "name": "Violin"},
    {"id": 42, "name": "Cello"},
    {"id": 46, "name": "Orchestral Harp"},
    {"id": 48, "name": "String Ensemble 1"},
    {"id": 56, "name": "Trumpet"},
    {"id": 65, "name": "Alto Sax"},
    {"id": 68, "name": "Oboe"},
    {"id": 71, "name": "Clarinet"},
    {"id": 73, "name": "Flute"},
    {"id": 79, "name": "Ocarina"},
]

VALID_INSTRUMENT_IDS = {inst["id"] for inst in INSTRUMENTS}
_INSTRUMENT_NAMES = {inst["id"]: inst["name"] for inst in INSTRUMENTS}

# Limit concurrent WebSocket generation streams per worker
_ws_semaphore = asyncio.Semaphore(5)


async def _save_to_gallery(db, model_id, instrument_id, instrument_name, midi_file, wav_file, temperature, num_notes):
    try:
        await db.execute(
            """INSERT INTO generated_melody
               (model_id, instrument_id, instrument_name,
                midi_file, wav_file, temperature, num_notes)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            model_id,
            instrument_id,
            instrument_name,
            midi_file,
            wav_file,
            temperature,
            num_notes,
        )
    except Exception as e:
        logger.error(f"Failed to save melody to gallery: {e}")


class GenerateRequest(BaseModel):
    model_id: str
    instrument: Optional[int] = 0
    temperature: Optional[float] = Field(default=0.8, gt=0.0, le=2.0)
    top_k: Optional[int] = Field(default=50, ge=0, le=500)
    top_p: Optional[float] = Field(default=0.95, gt=0.0, le=1.0)
    num_notes: Optional[int] = Field(default=500, ge=50, le=2000)
    seed_midi: Optional[str] = Field(default=None, max_length=1_400_000)

    def validated_seed_midi(self) -> str | None:
        """Return seed_midi after verifying it is valid base64, or None."""
        if not self.seed_midi:
            return None
        try:
            base64.b64decode(self.seed_midi, validate=True)
            return self.seed_midi
        except Exception:
            raise HTTPException(status_code=400, detail="seed_midi must be valid base64")


@router.get("/instruments")
async def get_instruments():
    return INSTRUMENTS


@router.get("/models")
async def get_models_list(request: Request):
    try:
        models = request.app.state.models
        if models is None:
            from app.src.services.melody_generator import get_available_models

            settings = request.app.state.settings
            models = await get_available_models(settings.model_dir)
            request.app.state.models = models

        model_list = []
        for model_id, bundle in models.items():
            model_list.append(
                {
                    "id": model_id,
                    "name": model_id,
                    "architecture": bundle.architecture,
                    "version": bundle.model_version,
                }
            )
        return model_list
    except Exception as e:
        logger.exception(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch models")


@router.post("/generate")
@limiter.limit("10/minute")
async def generate_melody(body: GenerateRequest, request: Request):
    try:
        model_id = body.model_id
        if not model_id:
            raise HTTPException(status_code=400, detail="No model_id provided")

        models = request.app.state.models
        settings = request.app.state.settings

        midi_program = body.instrument if body.instrument in VALID_INSTRUMENT_IDS else 0
        logger.info(
            f"Generate request: model={model_id}, instrument={midi_program}, "
            f"temp={body.temperature}, top_k={body.top_k}, top_p={body.top_p}, "
            f"num_notes={body.num_notes}"
        )

        start_time = time.monotonic()
        try:
            midi_file, wav_file = await asyncio.wait_for(
                generate_melody_service(
                    model_id,
                    models,
                    settings.output_dir,
                    settings.soundfont_path,
                    midi_program=midi_program,
                    num_notes=body.num_notes,
                    temperature=body.temperature,
                    top_k=body.top_k,
                    top_p=body.top_p,
                    seed_midi=body.validated_seed_midi(),
                ),
                timeout=600,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Generation timed out")

        duration_ms = round((time.monotonic() - start_time) * 1000)
        logger.info(f"Generation complete: model={model_id}, notes={body.num_notes}, duration={duration_ms}ms")

        midi_basename = os.path.basename(midi_file)
        wav_basename = os.path.basename(wav_file) if wav_file else None

        db = request.app.state.pg_db
        if db:
            instrument_name = _INSTRUMENT_NAMES.get(midi_program, "Unknown")
            await _save_to_gallery(
                db,
                model_id,
                midi_program,
                instrument_name,
                midi_basename,
                wav_basename,
                body.temperature,
                body.num_notes,
            )

        response = {
            "message": "Melody generated successfully",
            "midi_file": midi_basename,
        }
        if wav_file:
            response["wav_file"] = wav_basename

        return response
    except (HTTPException, ValueError):
        raise
    except Exception as e:
        logger.exception(f"Error generating melody: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while generating the melody")


@router.websocket("/generate/stream")
async def generate_melody_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming melody generation."""
    await websocket.accept()
    try:
        async with _ws_semaphore:
            config = await websocket.receive_json()

            if config.get("type") != "start_generation":
                await websocket.send_json({"type": "error", "message": "Expected start_generation message"})
                await websocket.close()
                return

            model_id = config.get("model_id")
            if not model_id:
                await websocket.send_json({"type": "error", "message": "No model_id provided"})
                await websocket.close()
                return

            models = websocket.app.state.models
            settings = websocket.app.state.settings

            if model_id not in models:
                await websocket.send_json({"type": "error", "message": f"Model not found: {model_id}"})
                await websocket.close()
                return

            num_notes = min(max(config.get("num_notes", 500), 50), 2000)
            temperature = min(max(config.get("temperature", 0.8), 0.1), 2.0)
            top_k = min(max(config.get("top_k", 50), 0), 500)
            top_p = min(max(config.get("top_p", 0.95), 0.01), 1.0)
            midi_program = config.get("instrument", 0)

            await websocket.send_json(
                {
                    "type": "generation_started",
                    "total_notes": num_notes,
                }
            )

            token_ids = None

            try:
                async with asyncio.timeout(300):  # 5 minute timeout
                    async for event in generate_melody_streaming(
                        model_id,
                        models,
                        num_notes=num_notes,
                        temperature=temperature,
                        top_k=top_k,
                        top_p=top_p,
                        midi_program=midi_program,
                    ):
                        if event.get("type") == "sequence_complete":
                            token_ids = event.get("token_ids")
                            continue
                        await websocket.send_json(event)
            except TimeoutError:
                await websocket.send_json({"type": "error", "message": "Generation timed out"})
                await websocket.close()
                return

            # Generate full MIDI/WAV for download
            output_dir = settings.output_dir
            os.makedirs(output_dir, exist_ok=True)
            timestamp = uuid.uuid4().hex[:12]
            midi_file = os.path.join(output_dir, f"generated_melody_{timestamp}.mid")
            wav_file = os.path.join(output_dir, f"generated_melody_{timestamp}.wav")

            bundle = models[model_id]
            tokenizer = bundle.tokenizer
            loop = asyncio.get_event_loop()

            if tokenizer and token_ids:
                await loop.run_in_executor(None, create_midi_from_tokens, token_ids, tokenizer, midi_file, midi_program)
            elif token_ids:
                # Transformer without tokenizer - should not happen in practice
                pass

            # Convert to WAV
            wav_path = None
            if settings.soundfont_path and os.path.exists(settings.soundfont_path) and os.path.exists(midi_file):
                await loop.run_in_executor(None, convert_midi_to_wav, midi_file, wav_file, settings.soundfont_path)
                wav_path = wav_file

            midi_basename = os.path.basename(midi_file)
            wav_basename = os.path.basename(wav_path) if wav_path else None

            db = getattr(websocket.app.state, "pg_db", None)
            if db:
                instrument_name = _INSTRUMENT_NAMES.get(midi_program, "Unknown")
                await _save_to_gallery(
                    db, model_id, midi_program, instrument_name, midi_basename, wav_basename, temperature, num_notes
                )

            response = {
                "type": "generation_complete",
                "midi_file": midi_basename,
            }
            if wav_path:
                response["wav_file"] = wav_basename
                response["download_url"] = f"/melody/download/{wav_basename}"

            await websocket.send_json(response)
            await websocket.close()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "An internal error occurred"})
            await websocket.close()
        except Exception:
            pass


@router.get("/gallery")
async def get_gallery(request: Request, limit: int = 20, offset: int = 0):
    db = request.app.state.pg_db
    rows = await db.fetch(
        """SELECT id, model_id, instrument_name, midi_file, wav_file, temperature, num_notes, created,
                  COUNT(*) OVER () AS total
           FROM generated_melody ORDER BY created DESC LIMIT $1 OFFSET $2""",
        min(limit, 50),
        max(offset, 0),
    )
    total = rows[0]["total"] if rows else 0
    return {
        "melodies": [{k: v for k, v in dict(r).items() if k != "total"} for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/download/{filename}")
@limiter.limit("30/minute")
async def download_file(filename: str, request: Request):
    settings = request.app.state.settings
    safe_name = os.path.basename(filename)
    if safe_name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = os.path.join(settings.output_dir, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_types = {
        ".mid": "audio/midi",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
    }
    ext = os.path.splitext(filename)[1].lower()
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(file_path, filename=filename, media_type=media_type)
