'use client';

const ModelSelector = ({ models, selectedModel, onSelectModel }) => {
  if (models.length === 0) {
    return <div className="mb-4">No models available</div>;
  }

  return (
    <div className="mb-4">
      <select
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        className="w-full p-2 text-base border border-primary rounded"
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
};

export default ModelSelector;
