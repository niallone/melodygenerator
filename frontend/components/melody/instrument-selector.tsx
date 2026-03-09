'use client';

import type { Instrument } from '../../types';

interface InstrumentSelectorProps {
  instruments: Instrument[];
  selectedInstrument: number;
  onSelectInstrument: (value: number) => void;
}

export default function InstrumentSelector({ instruments, selectedInstrument, onSelectInstrument }: InstrumentSelectorProps) {
  if (instruments.length === 0) {
    return <div className="mb-4 text-text-secondary dark:text-dark-text-secondary">No instruments available</div>;
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-text-secondary dark:text-dark-text-secondary mb-1.5">Instrument</label>
      <select
        value={selectedInstrument}
        onChange={(e) => onSelectInstrument(Number(e.target.value))}
        className="w-full p-2.5 text-sm bg-surface dark:bg-dark-surface-elevated text-text-primary dark:text-dark-text-primary border border-border dark:border-dark-border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
      >
        {instruments.map((inst) => (
          <option key={inst.id} value={inst.id}>
            {inst.name}
          </option>
        ))}
      </select>
    </div>
  );
}
