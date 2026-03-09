'use client';

import { memo, useCallback, type ChangeEvent, type Dispatch } from 'react';
import ConditionControls from './condition-controls';
import type { Conditions, GenerationAction } from '../../types';

interface AdvancedOptionsProps {
  temperature: number;
  topK: number;
  topP: number;
  numNotes: number;
  keySignature: string;
  tempo: string;
  style: string;
  conditions: Conditions | null;
  seedFileName: string;
  useStreaming: boolean;
  dispatch: Dispatch<GenerationAction>;
  onFileUpload: (e: ChangeEvent<HTMLInputElement>) => void;
  onClearSeed: () => void;
}

const AdvancedOptions = memo(function AdvancedOptions({
  temperature,
  topK,
  topP,
  numNotes,
  keySignature,
  tempo,
  style,
  conditions,
  seedFileName,
  useStreaming,
  dispatch,
  onFileUpload,
  onClearSeed,
}: AdvancedOptionsProps) {
  const handleTemperatureChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_PARAM', key: 'temperature', value: parseFloat(e.target.value) });
  }, [dispatch]);

  const handleTopKChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_PARAM', key: 'topK', value: parseInt(e.target.value) });
  }, [dispatch]);

  const handleTopPChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_PARAM', key: 'topP', value: parseFloat(e.target.value) });
  }, [dispatch]);

  const handleNumNotesChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_PARAM', key: 'numNotes', value: parseInt(e.target.value) });
  }, [dispatch]);

  const handleStreamingChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_PARAM', key: 'useStreaming', value: e.target.checked });
  }, [dispatch]);

  return (
    <div className="mb-4 p-5 border border-white/[0.08] rounded-xl space-y-5 bg-white/[0.03] transition-colors">
      <div>
        <label htmlFor="temperature-slider" className="block text-sm font-medium text-white mb-1.5">
          Temperature: {temperature.toFixed(2)}
        </label>
        <input
          id="temperature-slider"
          type="range"
          min="0.1"
          max="2.0"
          step="0.05"
          value={temperature}
          onChange={handleTemperatureChange}
          className="w-full"
          aria-label="Temperature"
        />
        <div className="flex justify-between text-xs text-white/50 mt-1">
          <span>Conservative (0.1)</span>
          <span>Creative (2.0)</span>
        </div>
      </div>

      <div>
        <label htmlFor="topk-slider" className="block text-sm font-medium text-white mb-1.5">
          Top-K: {topK}
        </label>
        <input
          id="topk-slider"
          type="range"
          min="0"
          max="500"
          step="10"
          value={topK}
          onChange={handleTopKChange}
          className="w-full"
          aria-label="Top-K sampling"
        />
        <div className="flex justify-between text-xs text-white/50 mt-1">
          <span>Off (0)</span>
          <span>500</span>
        </div>
      </div>

      <div>
        <label htmlFor="topp-slider" className="block text-sm font-medium text-white mb-1.5">
          Top-P (Nucleus): {topP.toFixed(2)}
        </label>
        <input
          id="topp-slider"
          type="range"
          min="0.1"
          max="1.0"
          step="0.05"
          value={topP}
          onChange={handleTopPChange}
          className="w-full"
          aria-label="Top-P nucleus sampling"
        />
        <div className="flex justify-between text-xs text-white/50 mt-1">
          <span>Focused (0.1)</span>
          <span>Full (1.0)</span>
        </div>
      </div>

      <div>
        <label htmlFor="numnotes-slider" className="block text-sm font-medium text-white mb-1.5">
          Notes: {numNotes}
        </label>
        <input
          id="numnotes-slider"
          type="range"
          min="50"
          max="2000"
          step="50"
          value={numNotes}
          onChange={handleNumNotesChange}
          className="w-full"
          aria-label="Number of notes"
        />
        <div className="flex justify-between text-xs text-white/50 mt-1">
          <span>50</span>
          <span>2000</span>
        </div>
      </div>

      <div>
        <label htmlFor="seed-midi-upload" className="block text-sm font-medium text-white mb-1.5">Continue from MIDI (optional)</label>
        <div className="flex items-center gap-2">
          <input
            id="seed-midi-upload"
            type="file"
            accept=".mid,.midi"
            onChange={onFileUpload}
            className="text-sm text-white/50"
            aria-label="Upload seed MIDI file"
          />
          {seedFileName && (
            <span className="text-sm flex items-center gap-1 text-white/50">
              {seedFileName}
              <button onClick={onClearSeed} className="text-red-400 cursor-pointer hover:opacity-70 transition-opacity" aria-label="Remove seed file">x</button>
            </span>
          )}
        </div>
      </div>

      {conditions && (
        <ConditionControls
          conditions={conditions}
          keySignature={keySignature}
          onKeyChange={(v) => dispatch({ type: 'SET_PARAM', key: 'keySignature', value: v })}
          tempo={tempo}
          onTempoChange={(v) => dispatch({ type: 'SET_PARAM', key: 'tempo', value: v })}
          style={style}
          onStyleChange={(v) => dispatch({ type: 'SET_PARAM', key: 'style', value: v })}
        />
      )}

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="streaming-toggle"
          checked={useStreaming}
          onChange={handleStreamingChange}
        />
        <label htmlFor="streaming-toggle" className="text-sm text-white">
          Stream generation (real-time playback)
        </label>
      </div>
    </div>
  );
});

export default AdvancedOptions;
