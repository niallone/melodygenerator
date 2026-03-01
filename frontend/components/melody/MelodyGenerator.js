'use client';

import { useEffect, useCallback, useReducer, useRef } from 'react';
import { useMelodyGenerator } from '../../hooks/useMelodyGenerator';
import { useStreamingGeneration } from '../../hooks/useStreamingGeneration';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import GenerationControls from './GenerationControls';
import AdvancedOptions from './AdvancedOptions';
import StreamingVisualiser from './StreamingVisualiser';
import { fetchModels, fetchInstruments, fetchConditions } from '../../utils/api';

const initialState = {
  models: [],
  instruments: [],
  conditions: null,
  selectedModel: '',
  selectedInstrument: 0,
  temperature: 0.8,
  topK: 50,
  topP: 0.95,
  numNotes: 500,
  keySignature: '',
  tempo: '',
  style: '',
  seedMidi: null,
  seedFileName: '',
  useStreaming: false,
  showAdvanced: false,
  isLoading: true,
  loadError: null,
};

function generationReducer(state, action) {
  switch (action.type) {
    case 'SET_PARAM':
      return { ...state, [action.key]: action.value };
    case 'SET_MODELS':
      return { ...state, models: action.value };
    case 'SET_INSTRUMENTS':
      return { ...state, instruments: action.value };
    case 'SET_CONDITIONS':
      return { ...state, conditions: action.value };
    case 'SET_SEED':
      return { ...state, seedMidi: action.midi, seedFileName: action.fileName };
    case 'CLEAR_SEED':
      return { ...state, seedMidi: null, seedFileName: '' };
    case 'SET_LOADING':
      return { ...state, isLoading: action.value };
    case 'SET_LOAD_ERROR':
      return { ...state, loadError: action.value };
    case 'RESET':
      return { ...initialState, models: state.models, instruments: state.instruments, conditions: state.conditions };
    default:
      return state;
  }
}

export function MelodyGenerator({ onGenerated }) {
  const [state, dispatch] = useReducer(generationReducer, initialState);
  const { generate, isGenerating, error } = useMelodyGenerator();
  const streaming = useStreamingGeneration();

  useEffect(() => {
    const controller = new AbortController();

    const loadData = async () => {
      try {
        dispatch({ type: 'SET_LOADING', value: true });
        const [fetchedModels, fetchedInstruments] = await Promise.all([
          fetchModels(),
          fetchInstruments(),
        ]);
        if (controller.signal.aborted) return;
        dispatch({ type: 'SET_MODELS', value: fetchedModels });
        dispatch({ type: 'SET_INSTRUMENTS', value: fetchedInstruments });

        try {
          const fetchedConditions = await fetchConditions();
          if (!controller.signal.aborted) {
            dispatch({ type: 'SET_CONDITIONS', value: fetchedConditions });
          }
        } catch {
          // Conditions endpoint may not exist for older API versions
        }

        dispatch({ type: 'SET_LOAD_ERROR', value: null });
      } catch (err) {
        if (!controller.signal.aborted) {
          console.error('Error loading data:', err);
          dispatch({ type: 'SET_LOAD_ERROR', value: 'Failed to load models. Please try again later.' });
        }
      } finally {
        if (!controller.signal.aborted) {
          dispatch({ type: 'SET_LOADING', value: false });
        }
      }
    };

    loadData();
    return () => controller.abort();
  }, []);

  const handleFileUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = btoa(
        new Uint8Array(reader.result).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );
      dispatch({ type: 'SET_SEED', midi: base64, fileName: file.name });
    };
    reader.readAsArrayBuffer(file);
  }, []);

  const clearSeedMidi = useCallback(() => {
    dispatch({ type: 'CLEAR_SEED' });
  }, []);

  const getGenerationOptions = useCallback(() => ({
    temperature: state.temperature,
    top_k: state.topK,
    top_p: state.topP,
    num_notes: state.numNotes,
    seed_midi: state.seedMidi,
    key_signature: state.keySignature || null,
    tempo: state.tempo ? parseInt(state.tempo) : null,
    style: state.style || null,
  }), [state.temperature, state.topK, state.topP, state.numNotes, state.seedMidi, state.keySignature, state.tempo, state.style]);

  // Track streaming completion to trigger onGenerated
  const wasStreamingRef = useRef(false);
  useEffect(() => {
    if (wasStreamingRef.current && !streaming.isStreaming) {
      onGenerated?.();
    }
    wasStreamingRef.current = streaming.isStreaming;
  }, [streaming.isStreaming, onGenerated]);

  const handleGenerate = useCallback(async () => {
    if (!state.selectedModel) return;

    if (state.useStreaming) {
      streaming.start(state.selectedModel, state.selectedInstrument, getGenerationOptions());
    } else {
      await generate(state.selectedModel, state.selectedInstrument, getGenerationOptions());
      onGenerated?.();
    }
  }, [state.selectedModel, state.selectedInstrument, state.useStreaming, streaming, generate, getGenerationOptions, onGenerated]);

  const isBusy = isGenerating || streaming.isStreaming;

  return (
    <section className="mb-8" aria-label="Melody Generator">
      {state.isLoading ? (
        <div className="flex justify-center items-center h-[50px]">
          <LoadingSpinner />
        </div>
      ) : state.loadError ? (
        <p className="text-error">{state.loadError}</p>
      ) : (
        <>
          <GenerationControls
            models={state.models}
            instruments={state.instruments}
            selectedModel={state.selectedModel}
            onSelectModel={(v) => dispatch({ type: 'SET_PARAM', key: 'selectedModel', value: v })}
            selectedInstrument={state.selectedInstrument}
            onSelectInstrument={(v) => dispatch({ type: 'SET_PARAM', key: 'selectedInstrument', value: v })}
          />

          <button
            onClick={() => dispatch({ type: 'SET_PARAM', key: 'showAdvanced', value: !state.showAdvanced })}
            className="text-sm text-primary mb-4 cursor-pointer hover:underline"
            aria-expanded={state.showAdvanced}
          >
            {state.showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>

          {state.showAdvanced && (
            <AdvancedOptions
              temperature={state.temperature}
              topK={state.topK}
              topP={state.topP}
              numNotes={state.numNotes}
              keySignature={state.keySignature}
              tempo={state.tempo}
              style={state.style}
              conditions={state.conditions}
              seedFileName={state.seedFileName}
              useStreaming={state.useStreaming}
              dispatch={dispatch}
              onFileUpload={handleFileUpload}
              onClearSeed={clearSeedMidi}
            />
          )}
        </>
      )}

      <Button onClick={handleGenerate} disabled={isBusy || !state.selectedModel || state.isLoading}>
        {isBusy ? <LoadingSpinner /> : state.useStreaming ? 'Stream Melody' : 'Generate New Melody'}
      </Button>

      {/* Streaming progress */}
      {streaming.isStreaming && (
        <div className="mt-4">
          <div className="text-sm mb-2">
            Generating: {streaming.progress}/{streaming.totalNotes} notes
          </div>
          <div
            className="w-full bg-light-gray rounded h-2"
            role="progressbar"
            aria-valuenow={streaming.progress}
            aria-valuemin={0}
            aria-valuemax={streaming.totalNotes}
          >
            <div
              className="bg-primary h-2 rounded transition-all"
              style={{ width: `${streaming.totalNotes ? (streaming.progress / streaming.totalNotes) * 100 : 0}%` }}
            />
          </div>
          <StreamingVisualiser notes={streaming.notes} />
        </div>
      )}

      {error && <p className="text-error mt-2">{error}</p>}
      {streaming.error && <p className="text-error mt-2">{streaming.error}</p>}
    </section>
  );
}
