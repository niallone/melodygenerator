export interface Model {
  id: string;
  name: string;
}

export interface Instrument {
  id: number;
  name: string;
}

export interface Conditions {
  keys?: string[];
  tempos?: number[];
  styles?: string[];
}

export interface Melody {
  id: number;
  name: string;
  url: string;
  midiUrl?: string;
}

export interface GalleryMelody {
  id: number;
  wav_file: string;
  midi_file: string;
  instrument_name: string;
  model_id: string;
  temperature: number;
  num_notes: number;
  created: string;
}

export interface GalleryResponse {
  melodies: GalleryMelody[];
  total: number;
}

export interface GenerationOptions {
  temperature?: number;
  top_k?: number;
  top_p?: number;
  num_notes?: number;
  seed_midi?: string | null;
  key_signature?: string | null;
  tempo?: number | null;
  style?: string | null;
}

export interface NoteEvent {
  pitch: number;
  duration: number;
  offset: number;
  velocity?: number;
  type?: string;
}

export interface StreamingStartedEvent {
  type: 'generation_started';
  total_notes: number;
}

export interface StreamingCompleteEvent {
  type: 'generation_complete';
  wav_file?: string;
  midi_file?: string;
}

export interface StreamingCallbacks {
  onStarted?: (data: StreamingStartedEvent) => void;
  onNote?: (data: NoteEvent) => void;
  onComplete?: (data: StreamingCompleteEvent) => void;
  onError?: (error: Error) => void;
  onClose?: (event: CloseEvent) => void;
}

export interface StreamingConnection {
  send: (data: Record<string, unknown>) => void;
  close: () => void;
  readonly readyState: number;
  onReady: (callback: () => void) => void;
}

export type GenerationStateKey =
  | 'selectedModel'
  | 'selectedInstrument'
  | 'temperature'
  | 'topK'
  | 'topP'
  | 'numNotes'
  | 'keySignature'
  | 'tempo'
  | 'style'
  | 'useStreaming'
  | 'showAdvanced';

export interface GenerationState {
  models: Model[];
  instruments: Instrument[];
  conditions: Conditions | null;
  selectedModel: string;
  selectedInstrument: number;
  temperature: number;
  topK: number;
  topP: number;
  numNotes: number;
  keySignature: string;
  tempo: string;
  style: string;
  seedMidi: string | null;
  seedFileName: string;
  useStreaming: boolean;
  showAdvanced: boolean;
  isLoading: boolean;
  loadError: string | null;
}

export type GenerationAction =
  | { type: 'SET_PARAM'; key: GenerationStateKey; value: string | number | boolean }
  | { type: 'SET_MODELS'; value: Model[] }
  | { type: 'SET_INSTRUMENTS'; value: Instrument[] }
  | { type: 'SET_CONDITIONS'; value: Conditions }
  | { type: 'SET_SEED'; midi: string; fileName: string }
  | { type: 'CLEAR_SEED' }
  | { type: 'SET_LOADING'; value: boolean }
  | { type: 'SET_LOAD_ERROR'; value: string | null }
  | { type: 'RESET' };
