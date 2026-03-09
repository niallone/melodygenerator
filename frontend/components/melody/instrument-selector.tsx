'use client';

import type { Instrument } from '../../types';

interface InstrumentSelectorProps {
  instruments: Instrument[];
  selectedInstrument: number;
  onSelectInstrument: (value: number) => void;
}

export default function InstrumentSelector({ instruments, selectedInstrument, onSelectInstrument }: InstrumentSelectorProps) {
  if (instruments.length === 0) {
    return <div className="mb-4 text-white/50">No instruments available</div>;
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-white/50 mb-1.5">Instrument</label>
      <select
        value={selectedInstrument}
        onChange={(e) => onSelectInstrument(Number(e.target.value))}
        className="w-full p-2.5 text-sm bg-white/[0.02] text-white border border-white/[0.08] rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
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
