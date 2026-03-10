import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MelodyGenerator } from '../../components/melody/melody-generator';

vi.mock('../../hooks/use-melody-generator', () => ({
  useMelodyGenerator: () => ({
    generate: vi.fn(),
    isGenerating: false,
    error: null,
  }),
}));

vi.mock('../../hooks/use-streaming-generation', () => ({
  useStreamingGeneration: () => ({
    start: vi.fn(),
    stop: vi.fn(),
    isStreaming: false,
    progress: 0,
    totalNotes: 0,
    notes: [],
    error: null,
  }),
}));

vi.mock('../../utils/api', () => ({
  fetchModels: vi.fn(),
  fetchInstruments: vi.fn(),
  fetchConditions: vi.fn(),
  WS_URL: 'ws://localhost:4050',
}));

import { fetchModels, fetchInstruments, fetchConditions } from '../../utils/api';

const mockFetchModels = fetchModels as ReturnType<typeof vi.fn>;
const mockFetchInstruments = fetchInstruments as ReturnType<typeof vi.fn>;
const mockFetchConditions = fetchConditions as ReturnType<typeof vi.fn>;

describe('MelodyGenerator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockFetchModels.mockReturnValue(new Promise(() => {}));
    mockFetchInstruments.mockReturnValue(new Promise(() => {}));
    mockFetchConditions.mockReturnValue(new Promise(() => {}));

    const { container } = render(<MelodyGenerator />);

    const loadingContainer = container.querySelector('.flex.justify-center.items-center');
    expect(loadingContainer).toBeInTheDocument();

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('shows error message when load fails', async () => {
    mockFetchModels.mockRejectedValue(new Error('Network error'));
    mockFetchInstruments.mockRejectedValue(new Error('Network error'));
    mockFetchConditions.mockRejectedValue(new Error('Network error'));

    render(<MelodyGenerator />);

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load models. Please try again later.'),
      ).toBeInTheDocument();
    });
  });
});
