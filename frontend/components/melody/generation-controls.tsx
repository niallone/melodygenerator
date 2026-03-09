'use client';

import { memo } from 'react';
import ModelSelector from './model-selector';
import InstrumentSelector from './instrument-selector';
import type { Model, Instrument } from '../../types';

interface GenerationControlsProps {
  models: Model[];
  instruments: Instrument[];
  selectedModel: string;
  onSelectModel: (value: string) => void;
  selectedInstrument: number;
  onSelectInstrument: (value: number) => void;
}

const GenerationControls = memo(function GenerationControls({
  models,
  instruments,
  selectedModel,
  onSelectModel,
  selectedInstrument,
  onSelectInstrument,
}: GenerationControlsProps) {
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
