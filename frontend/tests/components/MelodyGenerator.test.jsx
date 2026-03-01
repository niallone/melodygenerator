import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MelodyGenerator } from '../../components/melody/MelodyGenerator';

// Mock the hooks
vi.mock('../../hooks/useMelodyGenerator', () => ({
  useMelodyGenerator: () => ({
    generate: vi.fn(),
    isGenerating: false,
    error: null,
  }),
}));

vi.mock('../../hooks/useStreamingGeneration', () => ({
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

// Mock the API utilities
vi.mock('../../utils/api', () => ({
  fetchModels: vi.fn(),
  fetchInstruments: vi.fn(),
  fetchConditions: vi.fn(),
  WS_URL: 'ws://localhost:4050',
}));

import { fetchModels, fetchInstruments, fetchConditions } from '../../utils/api';

describe('MelodyGenerator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    // Make the fetches hang so loading state persists
    fetchModels.mockReturnValue(new Promise(() => {}));
    fetchInstruments.mockReturnValue(new Promise(() => {}));
    fetchConditions.mockReturnValue(new Promise(() => {}));

    const { container } = render(<MelodyGenerator />);

    // The loading spinner is rendered inside the loading state container
    const loadingContainer = container.querySelector('.flex.justify-center.items-center');
    expect(loadingContainer).toBeInTheDocument();

    // The spinner element itself (the animated div)
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('shows error message when load fails', async () => {
    fetchModels.mockRejectedValue(new Error('Network error'));
    fetchInstruments.mockRejectedValue(new Error('Network error'));
    fetchConditions.mockRejectedValue(new Error('Network error'));

    render(<MelodyGenerator />);

    await waitFor(() => {
      expect(
        screen.getByText('Failed to load models. Please try again later.')
      ).toBeInTheDocument();
    });
  });
});
