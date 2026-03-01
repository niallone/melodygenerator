'use client';

import { memo, useCallback } from 'react';
import ConditionControls from './ConditionControls';

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
}) {
  const handleTemperatureChange = useCallback((e) => {
    dispatch({ type: 'SET_PARAM', key: 'temperature', value: parseFloat(e.target.value) });
  }, [dispatch]);

  const handleTopKChange = useCallback((e) => {
    dispatch({ type: 'SET_PARAM', key: 'topK', value: parseInt(e.target.value) });
  }, [dispatch]);

  const handleTopPChange = useCallback((e) => {
    dispatch({ type: 'SET_PARAM', key: 'topP', value: parseFloat(e.target.value) });
  }, [dispatch]);

  const handleNumNotesChange = useCallback((e) => {
    dispatch({ type: 'SET_PARAM', key: 'numNotes', value: parseInt(e.target.value) });
  }, [dispatch]);

  const handleStreamingChange = useCallback((e) => {
    dispatch({ type: 'SET_PARAM', key: 'useStreaming', value: e.target.checked });
  }, [dispatch]);

  return (
    <div className="mb-4 p-4 border border-light-gray rounded space-y-4">
      {/* Temperature */}
      <div>
        <label htmlFor="temperature-slider" className="block text-sm mb-1">
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
        <div className="flex justify-between text-xs text-dark-gray">
          <span>Conservative (0.1)</span>
          <span>Creative (2.0)</span>
        </div>
      </div>

      {/* Top-K */}
      <div>
        <label htmlFor="topk-slider" className="block text-sm mb-1">
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
        <div className="flex justify-between text-xs text-dark-gray">
          <span>Off (0)</span>
          <span>500</span>
        </div>
      </div>

      {/* Top-P */}
      <div>
        <label htmlFor="topp-slider" className="block text-sm mb-1">
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
        <div className="flex justify-between text-xs text-dark-gray">
          <span>Focused (0.1)</span>
          <span>Full (1.0)</span>
        </div>
      </div>

      {/* Number of Notes */}
      <div>
        <label htmlFor="numnotes-slider" className="block text-sm mb-1">
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
        <div className="flex justify-between text-xs text-dark-gray">
          <span>50</span>
          <span>2000</span>
        </div>
      </div>

      {/* Seed MIDI upload */}
      <div>
        <label htmlFor="seed-midi-upload" className="block text-sm mb-1">Continue from MIDI (optional)</label>
        <div className="flex items-center gap-2">
          <input
            id="seed-midi-upload"
            type="file"
            accept=".mid,.midi"
            onChange={onFileUpload}
            className="text-sm"
            aria-label="Upload seed MIDI file"
          />
          {seedFileName && (
            <span className="text-sm flex items-center gap-1">
              {seedFileName}
              <button onClick={onClearSeed} className="text-error cursor-pointer" aria-label="Remove seed file">x</button>
            </span>
          )}
        </div>
      </div>

      {/* Condition Controls */}
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

      {/* Streaming toggle */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="streaming-toggle"
          checked={useStreaming}
          onChange={handleStreamingChange}
        />
        <label htmlFor="streaming-toggle" className="text-sm">
          Stream generation (real-time playback)
        </label>
      </div>
    </div>
  );
});

export default AdvancedOptions;
