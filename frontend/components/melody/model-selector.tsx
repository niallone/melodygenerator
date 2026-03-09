'use client';

import type { Model } from '../../types';

interface ModelSelectorProps {
  models: Model[];
  selectedModel: string;
  onSelectModel: (value: string) => void;
}

export default function ModelSelector({ models, selectedModel, onSelectModel }: ModelSelectorProps) {
  if (models.length === 0) {
    return <div className="mb-4 text-white/50">No models available</div>;
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-white/50 mb-1.5">Model</label>
      <select
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        className="w-full p-2.5 text-sm bg-white/[0.02] text-white border border-white/[0.08] rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
      >
        <option value="">Select a model</option>
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
    </div>
  );
}
