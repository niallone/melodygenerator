'use client';

import { memo } from 'react';
import ModelSelector from './ModelSelector';
import InstrumentSelector from './InstrumentSelector';

const GenerationControls = memo(function GenerationControls({
  models,
  instruments,
  selectedModel,
  onSelectModel,
  selectedInstrument,
  onSelectInstrument,
}) {
  return (
    <>
      <ModelSelector
        models={models}
        selectedModel={selectedModel}
        onSelectModel={onSelectModel}
      />
      <InstrumentSelector
        instruments={instruments}
        selectedInstrument={selectedInstrument}
        onSelectInstrument={onSelectInstrument}
      />
    </>
  );
});

export default GenerationControls;
