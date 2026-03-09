'use client';

import type { Conditions } from '../../types';

interface ConditionControlsProps {
  conditions: Conditions | null;
  keySignature: string;
  onKeyChange: (value: string) => void;
  tempo: string;
  onTempoChange: (value: string) => void;
  style: string;
  onStyleChange: (value: string) => void;
}

const selectClass = "w-full p-2.5 text-sm bg-surface dark:bg-dark-surface-elevated text-text-primary dark:text-dark-text-primary border border-border dark:border-dark-border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary";

export default function ConditionControls({
  conditions,
  keySignature,
  onKeyChange,
  tempo,
  onTempoChange,
  style,
  onStyleChange,
}: ConditionControlsProps) {
  if (!conditions) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">Conditions (optional)</h4>

      {conditions.keys && (
        <div>
          <label className="block text-sm text-text-secondary dark:text-dark-text-secondary mb-1">Key Signature</label>
          <select value={keySignature} onChange={(e) => onKeyChange(e.target.value)} className={selectClass}>
            <option value="">Any</option>
            {conditions.keys.map((key) => (
              <option key={key} value={key}>{key}</option>
            ))}
          </select>
        </div>
      )}

      {conditions.tempos && (
        <div>
          <label className="block text-sm text-text-secondary dark:text-dark-text-secondary mb-1">
            Tempo: {tempo || 'Any'} {tempo ? 'BPM' : ''}
          </label>
          <select value={tempo} onChange={(e) => onTempoChange(e.target.value)} className={selectClass}>
            <option value="">Any</option>
            {conditions.tempos.map((t) => (
              <option key={t} value={t}>{t} BPM</option>
            ))}
          </select>
        </div>
      )}

      {conditions.styles && (
        <div>
          <label className="block text-sm text-text-secondary dark:text-dark-text-secondary mb-1">Style</label>
          <select value={style} onChange={(e) => onStyleChange(e.target.value)} className={selectClass}>
            <option value="">Any</option>
            {conditions.styles.map((s) => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
