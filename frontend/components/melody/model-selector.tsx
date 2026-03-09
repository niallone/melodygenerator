'use client';

import type { Model } from '../../types';

interface ModelSelectorProps {
  models: Model[];
  selectedModel: string;
  onSelectModel: (value: string) => void;
}

export default function ModelSelector({ models, selectedModel, onSelectModel }: ModelSelectorProps) {
  if (models.length === 0) {
    return <div className="mb-4 text-text-secondary dark:text-dark-text-secondary">No models available</div>;
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-text-secondary dark:text-dark-text-secondary mb-1.5">Model</label>
      <select
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        className="w-full p-2.5 text-sm bg-surface dark:bg-dark-surface-elevated text-text-primary dark:text-dark-text-primary border border-border dark:border-dark-border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
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
