import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Research - AI Melody Generator',
  description:
    'Technical report on neural symbolic music generation: architecture decisions, tokenisation schemes, training methodology, and experimental results.',
};

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-indigo-400 hover:text-indigo-300 hover:underline transition-colors"
    >
      {children}
    </a>
  );
}

export default function Research() {
  return (
    <>
      {/* ─── HEADER ─── */}
      <section className="relative min-h-[60vh] flex items-end overflow-hidden pb-20 px-6 sm:px-10">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-1/3 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[120px]" />
          <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[100px]" />
        </div>
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />

        <div className="relative z-10 max-w-5xl mx-auto w-full">
          <h1 className="text-[clamp(2rem,5vw,4rem)] font-bold leading-[1] tracking-tight mb-6">
            Autoregressive Symbolic Music Generation
            <br />
            <span className="text-white/40">with LSTM and Transformer Architectures</span>
          </h1>
          <p className="text-lg text-white/50 max-w-3xl font-light leading-relaxed">
            This document describes the design, training, and evaluation of eight model versions
            developed for monophonic melody generation from MIDI data. It covers the evolution from a
            baseline LSTM to a 34M-parameter Transformer with REMI tokenisation and BPE compression,
            and reports observations from each iteration.
          </p>
        </div>
      </section>

      {/* ─── 1. PROBLEM STATEMENT ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-12 gap-12">
          <div className="sm:col-span-4">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
              1. Problem
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Problem
              <br />statement
            </h2>
          </div>
          <div className="sm:col-span-8 space-y-6 text-white/50 text-lg font-light leading-relaxed">
            <p>
              The task is next-token prediction over symbolic music sequences. Given a sequence of
              tokens representing musical events, the model predicts a probability distribution over
              the vocabulary for the next token. At inference time, tokens are sampled autoregressively
              from this distribution to produce novel sequences.
            </p>
            <p>
              The input representation is symbolic MIDI, not audio. Each note is a discrete event with
              pitch, onset time, duration, and velocity. The output is a MIDI file that can be
              rendered to audio, edited in a DAW, or transposed to a different key. The model has no
              access to audio signals and learns structure entirely from the symbolic representation.
            </p>
            <p>
              This differs from waveform generation systems (Suno, Udio, MusicGen) which produce
              finished audio. Symbolic generation preserves editability at the cost of requiring a
              separate synthesis step.
            </p>
          </div>
        </div>
      </section>

      {/* ─── 2. RELATED WORK ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            2. Related work
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            Prior work
          </h2>

          <div className="space-y-12">
            <div>
              <h3 className="text-lg font-bold mb-4">2.1 Attention mechanisms for music</h3>
              <p className="text-white/50 leading-relaxed mb-4">
                <ExtLink href="https://arxiv.org/abs/1809.04281">
                  Huang et al. (2019)
                </ExtLink>{' '}
                demonstrated that self-attention captures long-range musical structure more effectively
                than recurrent networks. Their Music Transformer used relative positional encoding to
                learn interval relationships rather than absolute positions, which is musically
                motivated: a perfect fifth is a perfect fifth regardless of the starting pitch.
              </p>
              <p className="text-white/50 leading-relaxed">
                This work motivated the transition from LSTM to Transformer in V7. However, the
                implementation here uses Rotary Position Embeddings (RoPE){' '}
                <ExtLink href="https://arxiv.org/abs/2104.09864">[Su et al., 2021]</ExtLink> instead
                of the relative attention scheme from the original paper. RoPE encodes position by
                rotating query and key vectors, producing a natural attention decay with distance at
                lower computational cost.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">2.2 REMI tokenisation</h3>
              <p className="text-white/50 leading-relaxed mb-4">
                <ExtLink href="https://arxiv.org/abs/2002.00212">
                  Huang and Yang (2020)
                </ExtLink>{' '}
                introduced REMI (REvamped MIDI-derived Events), a tokenisation scheme that encodes
                musical events as typed tokens: Bar, Position, Pitch, Velocity, Duration, Tempo, and
                Chord. This replaced earlier approaches that treated MIDI as a flat sequence of
                note-on/note-off events or pitch strings.
              </p>
              <p className="text-white/50 leading-relaxed">
                REMI makes musical structure explicit in the token stream. A note is no longer a
                single pitch token but a structured group of tokens encoding when it occurs, how loud
                it is, and how long it lasts. This was adopted in V6 using the MidiTok library with
                32 velocity levels, chord detection, tempo tokens, and rest tokens (a MidiTok
                extension not in the original REMI specification).
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">2.3 Subword compression for music</h3>
              <p className="text-white/50 leading-relaxed mb-4">
                <ExtLink href="https://arxiv.org/abs/2301.11975">
                  Fradet et al. (2023)
                </ExtLink>{' '}
                applied Byte Pair Encoding (BPE){' '}
                <ExtLink href="https://arxiv.org/abs/1508.07909">[Sennrich et al., 2016]</ExtLink>{' '}
                to REMI token sequences. BPE iteratively merges the most frequent token pairs into
                single tokens, compressing common multi-token note events (e.g., Position + Pitch +
                Velocity + Duration) into atomic units. This increases the musical context visible
                within a fixed sequence length.
              </p>
              <p className="text-white/50 leading-relaxed">
                BPE was adopted in V7 with a learned vocabulary of 512 tokens, and expanded to 1024
                in V8 to accommodate patterns from a larger training corpus.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">2.4 Architectural components from LLM research</h3>
              <p className="text-white/50 leading-relaxed">
                The Transformer architecture draws on several components developed for language
                modelling: SwiGLU feed-forward layers{' '}
                <ExtLink href="https://arxiv.org/abs/2002.05202">[Shazeer, 2020]</ExtLink>, RMSNorm{' '}
                <ExtLink href="https://arxiv.org/abs/1910.07467">[Zhang and Sennrich, 2019]</ExtLink>
                , and weight tying between input embeddings and the output projection{' '}
                <ExtLink href="https://arxiv.org/abs/1608.05859">[Press and Wolf, 2017]</ExtLink>.
                The learning rate schedule follows warmup followed by cosine decay{' '}
                <ExtLink href="https://arxiv.org/abs/1608.03983">
                  [Loshchilov and Hutter, 2016]
                </ExtLink>
                . These are standard choices in current Transformer training and are not specific to
                music.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 3. TOKENISATION ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute top-0 left-0 w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[120px]" />

        <div className="relative max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4">
            3. Tokenisation
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            Input representation
          </h2>
          <p className="text-white/50 max-w-2xl text-lg font-light mb-16">
            Three tokenisation strategies were used across model versions, each encoding progressively
            more musical information.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-white/[0.06] rounded-xl overflow-hidden">
            {[
              {
                era: 'V2\u2013V5',
                name: 'Pitch strings',
                tokens: '59\u20131,279',
                desc: 'Notes represented as music21 pitch names (e.g., "C4", "F#3") and chords as dot-separated integers. No explicit encoding of timing, velocity, or dynamics. Temporal structure learned implicitly from position in the sequence.',
              },
              {
                era: 'V6',
                name: 'REMI',
                tokens: '362',
                desc: 'Typed tokens: Bar, Position, Pitch, Velocity (32 levels), Duration, Tempo, Chord, Rest. Musical structure made explicit. Vocabulary decreased despite encoding strictly more information, because the typed scheme is more efficient than enumerating all observed pitch/chord combinations.',
              },
              {
                era: 'V7\u2013V8',
                name: 'REMI + BPE',
                tokens: '512\u20131,024',
                desc: 'BPE compression applied to REMI sequences. Frequently co-occurring token groups (e.g., a note event: Position + Pitch + Velocity + Duration) merged into single tokens. A 256-token BPE sequence covers approximately 2\u20133x more musical content than 256 raw REMI tokens.',
              },
            ].map((t) => (
              <div key={t.name} className="p-8 bg-white/[0.02]">
                <span className="text-xs text-indigo-400 font-mono mb-4 block">{t.era}</span>
                <h3 className="text-xl font-bold mb-2">{t.name}</h3>
                <p className="text-sm text-white/40 leading-relaxed mb-6">{t.desc}</p>
                <p className="text-3xl font-bold bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent font-mono">
                  {t.tokens}
                </p>
                <p className="text-xs text-white/30 mt-1">tokens</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── 4. MODEL ARCHITECTURES ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            4. Architecture
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            Model architectures
          </h2>

          <div className="space-y-16">
            {/* LSTM */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-12">
              <div className="sm:col-span-4">
                <h3 className="text-2xl font-bold mb-2">4.1 MelodyLSTM</h3>
                <p className="text-sm text-white/30 font-mono">V1\u2013V6</p>
              </div>
              <div className="sm:col-span-8 space-y-4 text-white/50 leading-relaxed">
                <p>
                  Three-layer LSTM. V1 through V4 used hidden units of [256, 512, 256] with
                  float-normalised pitch input (dividing by vocabulary size). V5 widened to
                  [512, 512, 512]. V6 added a learned embedding layer (128 dimensions), replacing
                  float normalisation. The final hidden state is projected through a linear layer to
                  the vocabulary size.
                </p>
                <p>
                  V1 through V5 were trained with TensorFlow/Keras and later converted to PyTorch.
                  V6 was the first version trained natively in PyTorch. The codebase includes support
                  for multi-head self-attention over the LSTM output, but no shipped model was
                  trained with this feature enabled.
                </p>
                <p>
                  The LSTM processes sequences of length 100 with stride 1 during training. At
                  inference, a seed sequence (randomly selected from training data) is extended
                  autoregressively using a sliding window.
                </p>
              </div>
            </div>

            {/* Transformer */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-12">
              <div className="sm:col-span-4">
                <h3 className="text-2xl font-bold mb-2">4.2 MusicTransformer</h3>
                <p className="text-sm text-white/30 font-mono">V7\u2013V8</p>
              </div>
              <div className="sm:col-span-8 space-y-4 text-white/50 leading-relaxed">
                <p>
                  8-layer decoder-only Transformer with 8 attention heads, 512 model dimension, and
                  2048 feed-forward dimension. Approximately 34 million parameters.
                </p>
                <div className="grid grid-cols-2 gap-4 my-6">
                  {[
                    {
                      name: 'RoPE',
                      desc: 'Rotary positional encoding. Position encoded by rotating query/key vectors in complex plane. Auto-extending cache for variable sequence lengths.',
                    },
                    {
                      name: 'SwiGLU',
                      desc: 'Gated feed-forward: W\u2082(SiLU(xW\u2081) \u2299 xW\u2083). Three weight matrices instead of two.',
                    },
                    {
                      name: 'RMSNorm',
                      desc: 'Pre-norm without mean centering. Applied before both attention and feed-forward sublayers.',
                    },
                    {
                      name: 'Weight tying',
                      desc: 'Token embedding and output projection share weights. Reduces parameters and regularises.',
                    },
                  ].map((item) => (
                    <div
                      key={item.name}
                      className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.08]"
                    >
                      <h4 className="text-sm font-bold mb-2 font-mono">{item.name}</h4>
                      <p className="text-xs text-white/40 leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
                <p>
                  Causal masking prevents attention to future positions. At inference, KV caching
                  stores previous key/value projections so each autoregressive step only computes
                  attention for the new token. The cache resets when the sequence exceeds
                  max_seq_len (512).
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 5. TRAINING ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] rounded-full bg-indigo-600/10 blur-[120px]" />

        <div className="relative max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4">5. Training</p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            Training methodology
          </h2>

          <div className="space-y-12">
            <div>
              <h3 className="text-lg font-bold mb-4">5.1 Data pipeline</h3>
              <p className="text-white/50 leading-relaxed mb-4">
                MIDI files are split into training and validation sets (90/10) before any
                augmentation to prevent data leakage. Each MIDI file is then augmented via pitch
                transposition before tokenisation: the score is shifted by a random number of
                semitones within +/-6, producing up to 2 augmented copies per original. This
                approximately triples the effective dataset size while preserving all structural
                relationships (a melody transposed to a different key is musically equivalent).
                Files are then tokenised (pitch-string or REMI depending on version).
              </p>
              <p className="text-white/50 leading-relaxed">
                Token sequences are then sliced into fixed-length windows using a sliding window with
                configurable stride. The LSTM uses stride 1 (dense overlap, sequence length 100). The
                Transformer uses stride 64 (sequence length 256). For the LSTM, the target is the
                single next token. For the Transformer, the target is the full sequence shifted by one
                position (causal language modelling loss at all positions).
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">5.2 Hyperparameters</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-white/[0.06] rounded-xl overflow-hidden">
                <div className="p-8 bg-white/[0.02]">
                  <p className="text-xs text-indigo-400 font-mono mb-4">LSTM (V6)</p>
                  <div className="space-y-3 text-sm">
                    {[
                      ['Layers', '3x LSTM [512, 512, 512]'],
                      ['Embedding', '128 dim (V6 only)'],
                      ['Sequence length', '100'],
                      ['Stride', '1'],
                      ['Batch size', '256'],
                      ['Learning rate', '4e-3'],
                      ['Optimiser', 'AdamW (wd=0.01)'],
                      ['LR schedule', 'Cosine annealing'],
                      ['Gradient clipping', 'max norm 1.0'],
                      ['Early stopping', '10 epochs patience'],
                      ['Augmentation', '2x, +/-6 semitones'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-4">
                        <span className="text-white/30">{k}</span>
                        <span className="text-white/70 font-mono text-xs text-right">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-8 bg-white/[0.02]">
                  <p className="text-xs text-indigo-400 font-mono mb-4">Transformer (V7/V8)</p>
                  <div className="space-y-3 text-sm">
                    {[
                      ['Layers', '8 transformer blocks'],
                      ['Attention heads', '8'],
                      ['d_model', '512'],
                      ['d_ff', '2048 (SwiGLU)'],
                      ['Sequence length', '256'],
                      ['Stride', '64'],
                      ['Batch size', '64 (accum 2)'],
                      ['Learning rate', '3e-4'],
                      ['Optimiser', 'AdamW (wd=0.01)'],
                      ['LR schedule', 'Warmup + cosine'],
                      ['Warmup', '2000 (V7) / 4000 (V8)'],
                      ['Early stopping', '15 epochs patience'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-4">
                        <span className="text-white/30">{k}</span>
                        <span className="text-white/70 font-mono text-xs text-right">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">5.3 Training data</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.08]">
                      <th className="text-left py-3 pr-4 text-white/30 font-medium">Model</th>
                      <th className="text-left py-3 pr-4 text-white/30 font-medium">Genre</th>
                      <th className="text-left py-3 pr-4 text-white/30 font-medium">Tracks</th>
                      <th className="text-left py-3 pr-4 text-white/30 font-medium">Tokeniser</th>
                      <th className="text-left py-3 text-white/30 font-medium">Vocab</th>
                    </tr>
                  </thead>
                  <tbody className="text-white/50">
                    {[
                      ['V2', 'R&B / 90s hip-hop', '24', 'Pitch strings', '59'],
                      ['V3', 'Dance', '~200', 'Pitch strings', '635'],
                      ['V4', 'Jazz', '~120', 'Pitch strings', '1,279'],
                      ['V5', 'Mixed', '275', 'Pitch strings', '629'],
                      ['V6', 'Mixed', '275', 'REMI', '362'],
                      ['V7', 'Mixed', '275', 'REMI + BPE', '512'],
                      ['V8', 'Mixed + classical', '275 + MAESTRO', 'REMI + BPE', '1,024'],
                    ].map(([model, genre, tracks, tok, vocab]) => (
                      <tr key={model} className="border-b border-white/[0.04]">
                        <td className="py-3 pr-4 font-mono text-white/70">{model}</td>
                        <td className="py-3 pr-4">{genre}</td>
                        <td className="py-3 pr-4 font-mono">{tracks}</td>
                        <td className="py-3 pr-4">{tok}</td>
                        <td className="py-3 font-mono">{vocab}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-white/30 mt-4">
                V8 includes the{' '}
                <ExtLink href="https://arxiv.org/abs/1810.12247">MAESTRO dataset</ExtLink>{' '}
                (v3): 1,276 competition piano performances from the International Piano-e-Competition.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 6. SAMPLING ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-12 gap-12">
          <div className="sm:col-span-4">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
              6. Sampling
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Decoding
              <br />strategy
            </h2>
          </div>
          <div className="sm:col-span-8">
            <p className="text-white/50 leading-relaxed mb-8">
              At each autoregressive step, the model produces a logit vector over the vocabulary. Three
              transformations are applied before sampling:
            </p>
            <div className="space-y-8">
              {[
                {
                  name: 'Temperature',
                  range: '0.1\u20132.0',
                  dflt: '0.8',
                  desc: 'Logits are divided by the temperature value before softmax. Values below 1.0 sharpen the distribution (more deterministic). Values above 1.0 flatten it (more diverse). This is applied first.',
                },
                {
                  name: 'Top-k',
                  range: '0\u2013500',
                  dflt: '50',
                  desc: 'All tokens outside the k highest-probability candidates are masked to negative infinity. This truncates the long tail of low-probability tokens that can produce incoherent output.',
                },
                {
                  name: 'Top-p (nucleus)',
                  range: '0.01\u20131.0',
                  dflt: '0.95',
                  desc: 'Tokens are sorted by probability and included until the cumulative probability exceeds p. This adapts the candidate set size dynamically: fewer candidates when the model is confident, more when uncertain.',
                },
              ].map((p) => (
                <div key={p.name} className="flex gap-6">
                  <div className="flex-shrink-0 w-20 pt-1">
                    <p className="text-xs text-white/40 font-mono">{p.dflt}</p>
                    <p className="text-[10px] text-white/25 font-mono mt-0.5">{p.range}</p>
                  </div>
                  <div className="flex-1 border-l border-white/[0.08] pl-6">
                    <h3 className="font-bold mb-1">{p.name}</h3>
                    <p className="text-sm text-white/50 leading-relaxed font-light">{p.desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-white/50 leading-relaxed mt-8">
              If both top-k and top-p mask all tokens (possible with aggressive settings), the
              implementation falls back to uniform sampling over the first k token indices, or the
              full vocabulary if top-k is disabled.
            </p>
          </div>
        </div>
      </section>

      {/* ─── 7. EVALUATION ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-12 gap-12">
          <div className="sm:col-span-4">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
              7. Evaluation
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Evaluation
              <br />metrics
            </h2>
          </div>
          <div className="sm:col-span-8 space-y-8">
            {[
              {
                name: 'Perplexity',
                desc: 'exp(cross-entropy loss) on held-out validation data. Measures how well the model predicts the next token. V7 reached validation perplexity of approximately 1.1.',
              },
              {
                name: 'N-gram repetition',
                desc: 'Computed at 2, 4, 8, and 16-gram levels over generated sequences. High repetition indicates the model is stuck in loops. REMI tokenisation reduced repetition relative to pitch-string encoding, because explicit timing tokens break up otherwise identical pitch sequences.',
              },
              {
                name: 'Compression ratio',
                desc: 'Ratio of unique n-grams to total n-grams in generated output. Values close to 1.0 indicate high diversity. Low values indicate heavy repetition. Used as a quick diagnostic during training.',
              },
              {
                name: 'Pitch distribution',
                desc: 'Histogram comparison between generated output and training data. Checks for mode collapse (over-representing a few pitches) and out-of-range values. A well-trained model should approximate the training distribution without memorising it.',
              },
            ].map((metric) => (
              <div key={metric.name} className="flex gap-6">
                <div className="flex-shrink-0 w-28 pt-1">
                  <p className="text-sm font-bold font-mono text-white/70">{metric.name}</p>
                </div>
                <div className="flex-1 border-l border-white/[0.08] pl-6">
                  <p className="text-sm text-white/50 leading-relaxed font-light">{metric.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── 8. EXPERIMENTAL RESULTS ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            8. Experiments
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            Experimental results
          </h2>
          <p className="text-white/50 max-w-2xl text-lg font-light mb-16">
            Eight model versions were trained sequentially. Each version changed one or two variables
            from the previous. The following summarises the progression and observations.
          </p>

          <div className="space-y-0 border border-white/[0.06] rounded-xl overflow-hidden">
            {[
              {
                version: 'V1',
                title: 'Baseline LSTM',
                arch: 'LSTM [256, 512, 256], float input, TF/Keras',
                detail:
                  'Initial proof of concept. Float-normalised pitch input (dividing by vocabulary size), no embedding layer. Produced vaguely musical output without coherent phrase structure. This version has since been lost but established that the autoregressive approach was viable.',
              },
              {
                version: 'V2',
                title: 'Genre-specific data',
                arch: 'LSTM [256, 512, 256], float input, TF/Keras',
                detail:
                  'Same architecture as V1. Trained on 24 R&B/hip-hop tracks. Vocabulary of 59 tokens due to limited harmonic complexity.',
              },
              {
                version: 'V3',
                title: 'Increased training data',
                arch: 'LSTM [256, 512, 256], float input, TF/Keras',
                detail:
                  'Same architecture as V2, trained on ~200 dance tracks. Vocabulary grew to 635 tokens. More data improved diversity but the model tended toward repetitive loops. The pitch-string encoding struggled with the harmonic variety in the dataset.',
              },
              {
                version: 'V4',
                title: 'Jazz dataset',
                arch: 'LSTM [256, 512, 256], float input, TF/Keras',
                detail:
                  'Same architecture as V3. Trained on ~120 jazz tracks. Vocabulary reached 1,279 tokens due to the combinatorial explosion of jazz chord voicings. The vocabulary size became a clear bottleneck for this architecture.',
              },
              {
                version: 'V5',
                title: 'Wider LSTM, mixed-genre training',
                arch: 'LSTM [512, 512, 512], float input, TF/Keras',
                detail:
                  'LSTM hidden units widened from [256, 512, 256] to [512, 512, 512]. Combined all 275 tracks across genres into a single training set. Vocabulary 629 tokens. Output quality was acceptable but had reached the ceiling of pitch-string encoding and float normalisation.',
              },
              {
                version: 'V6',
                title: 'PyTorch, embeddings, REMI tokenisation',
                arch: 'LSTM [512, 512, 512], embedding dim=128, REMI, PyTorch',
                detail:
                  'Rewritten in PyTorch. Added a learned embedding layer (128 dimensions), replacing float normalisation. Switched from pitch-string to REMI tokenisation. Vocabulary dropped from 629 to 362 while encoding timing, velocity, dynamics, and tempo. Output quality improved substantially. This confirmed that the input representation was the primary constraint, not the model capacity.',
              },
              {
                version: 'V7',
                title: 'Transformer architecture, BPE compression',
                arch: 'Transformer (8L/8H/512d), REMI + BPE 512',
                detail:
                  'Replaced LSTM with an 8-layer Transformer. Added RoPE, SwiGLU, RMSNorm, weight tying. Applied BPE (512 vocab) over REMI tokens. Sequence length increased to 256. Linear warmup (2000 steps) followed by cosine decay. Gradient accumulation (2 steps) for effective batch size of 128. Early-stopped at epoch 45 with best validation loss of 0.0952 (at epoch 30).',
              },
              {
                version: 'V8',
                title: 'Expanded vocabulary and dataset',
                arch: 'Transformer (8L/8H/512d), REMI + BPE 1024',
                detail:
                  'Same architecture as V7. BPE vocabulary doubled to 1024. Training data expanded with MAESTRO dataset (1,276 classical performances). Warmup increased to 4000 steps. Ran all 100 training epochs without early stopping, suggesting the model continued to benefit from the larger dataset throughout training.',
              },
            ].map((v) => (
              <div
                key={v.version}
                className="p-8 border-b border-white/[0.06] last:border-b-0"
              >
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0 w-12">
                    <span className="text-xl font-bold font-mono bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent">
                      {v.version}
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold mb-1">{v.title}</h3>
                    <p className="text-xs text-white/30 font-mono mb-3">{v.arch}</p>
                    <p className="text-sm text-white/50 leading-relaxed">{v.detail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── 9. OBSERVATIONS ─── */}
      <section className="border-t border-white/[0.06] bg-white/[0.02] py-24 px-6 sm:px-10">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            9. Discussion
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            Observations
          </h2>

          <div className="space-y-12">
            {[
              {
                heading: 'Tokenisation had more impact than model capacity',
                body: 'V5 and V6 use the same LSTM dimensions and training data. V6 changed three things simultaneously: the framework (TensorFlow to PyTorch), the input representation (float normalisation to learned embeddings), and the tokenisation scheme (pitch strings to REMI). Despite these combined changes, the most impactful was tokenisation: vocabulary dropped from 629 to 362 while encoding strictly more musical information. This is consistent with findings in NLP where input representation improvements outweigh model scaling.',
              },
              {
                heading: 'Genre-specific training had diminishing returns at this data scale',
                body: 'V2 through V4 were genre-specific (R&B, dance, jazz). V5 combined all genres. With fewer than 300 MIDI files total, the diversity of the combined dataset outweighed the benefit of genre focus. Genre-specific models may become worthwhile at dataset sizes of thousands of tracks per genre.',
              },
              {
                heading: 'Widening the LSTM had limited returns',
                body: 'V5 increased hidden units from [256, 512, 256] to [512, 512, 512] and combined all genres. This improved output quality modestly, but the fundamental limitation was the pitch-string representation and float normalisation, not the model capacity. The recurrent bottleneck also remained: all context must pass through the hidden state sequentially. The Transformer in V7 removed this bottleneck by allowing direct attention between any pair of positions.',
              },
              {
                heading: 'BPE compression increased effective context at negligible cost',
                body: 'Applying BPE over REMI tokens compressed multi-token note events into single tokens. A fixed-length window of 256 BPE tokens covers 2-3x more musical content than 256 raw REMI tokens. The encoding/decoding overhead is negligible. V8 doubled the BPE vocabulary (512 to 1024) to accommodate the more complex patterns in the MAESTRO dataset.',
              },
              {
                heading: 'Data augmentation was necessary to prevent overfitting',
                body: 'Pitch transposition (+/-6 semitones, up to 2 augmented copies per file) approximately tripled the effective dataset. Without augmentation, models overfit rapidly on the relatively small training sets. The augmentation is musically valid because transposition preserves all structural relationships between notes.',
              },
              {
                heading: 'V8 did not early-stop, unlike V7',
                body: 'V7 early-stopped at epoch 45 of 100 with best validation loss 0.0952 (at epoch 30). V8, with the same architecture but a larger dataset and vocabulary, ran all 100 epochs. This suggests V7 was data-limited and V8 had enough data to continue learning throughout the full training run.',
              },
            ].map((finding, i) => (
              <div key={i} className="grid grid-cols-1 sm:grid-cols-12 gap-6 sm:gap-12">
                <div className="sm:col-span-4">
                  <h3 className="text-lg font-bold leading-tight">{finding.heading}</h3>
                </div>
                <div className="sm:col-span-8">
                  <p className="text-white/50 leading-relaxed">{finding.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── 10. LIMITATIONS & FUTURE WORK ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-indigo-600/10 blur-[120px]" />

        <div className="relative max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            10. Limitations
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            Limitations and future work
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-white/[0.06] rounded-xl overflow-hidden">
            {[
              {
                name: 'Single-track generation',
                desc: 'The model produces a single melodic line. Multi-track generation (melody, bass, chords, drums) would require interleaved token representations or a multi-stream architecture.',
              },
              {
                name: 'Limited training data',
                desc: 'The primary dataset is 275 MIDI files. While MAESTRO adds classical performances for V8, the total training data is small by modern standards. Scaling to tens of thousands of curated MIDI files would likely improve both quality and diversity.',
              },
              {
                name: 'No model-level conditioning',
                desc: 'The API supports key, tempo, and style parameters, but the models do not yet use these as conditioning inputs. Prefix tokens or cross-attention over condition embeddings are two approaches under consideration.',
              },
              {
                name: 'Evaluation is primarily automated',
                desc: 'Perplexity, n-gram repetition, and pitch distribution are useful diagnostics but do not directly measure musical quality. Human evaluation or a learned critic model would provide stronger signal.',
              },
              {
                name: 'No music-specific positional encoding',
                desc: 'RoPE encodes sequential position but not musical concepts like beat position or bar structure. The original Music Transformer used relative position encodings designed for pitch intervals. Combining RoPE with music-aware relative encoding could improve harmonic coherence.',
              },
              {
                name: 'No fine-tuning from user feedback',
                desc: 'The gallery collects generated melodies but does not capture user preferences. A rating system could provide signal for RLHF-style fine-tuning on perceived musical quality.',
              },
            ].map((item) => (
              <div key={item.name} className="p-8 bg-white/[0.02]">
                <h3 className="font-bold mb-2">{item.name}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── REFERENCES ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">
            References
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-12">Bibliography</h2>

          <div className="space-y-6">
            {[
              {
                ref: 'Huang, C-Z. A., Vaswani, A., Uszkoreit, J., Shazeer, N., Simon, I., Hawthorne, C., Dai, A., Hoffman, M., Dinculescu, M., Eck, D. (2019). Music Transformer: Generating Music with Long-Term Structure.',
                url: 'https://arxiv.org/abs/1809.04281',
              },
              {
                ref: 'Huang, Y-S., Yang, Y-H. (2020). Pop Music Transformer: Beat-based Modeling and Generation of Expressive Pop Piano Compositions.',
                url: 'https://arxiv.org/abs/2002.00212',
              },
              {
                ref: 'Fradet, N., Gutowski, N., et al. (2023). Byte Pair Encoding for Symbolic Music.',
                url: 'https://arxiv.org/abs/2301.11975',
              },
              {
                ref: 'Hawthorne, C., Stasyuk, A., Roberts, A., Simon, I., Huang, C-Z. A., Dieleman, S., Elsen, E., Engel, J., Eck, D. (2019). Enabling Factorized Piano Music Modeling and Generation with the MAESTRO Dataset.',
                url: 'https://arxiv.org/abs/1810.12247',
              },
              {
                ref: 'Su, J., Lu, Y., Pan, S., Murtadha, A., Wen, B., Liu, Y. (2021). RoFormer: Enhanced Transformer with Rotary Position Embedding.',
                url: 'https://arxiv.org/abs/2104.09864',
              },
              {
                ref: 'Shazeer, N. (2020). GLU Variants Improve Transformer.',
                url: 'https://arxiv.org/abs/2002.05202',
              },
              {
                ref: 'Zhang, B., Sennrich, R. (2019). Root Mean Square Layer Normalization.',
                url: 'https://arxiv.org/abs/1910.07467',
              },
              {
                ref: 'Press, O., Wolf, L. (2017). Using the Output Embedding to Improve Language Models.',
                url: 'https://arxiv.org/abs/1608.05859',
              },
              {
                ref: 'Sennrich, R., Haddow, B., Birch, A. (2016). Neural Machine Translation of Rare Words with Subword Units.',
                url: 'https://arxiv.org/abs/1508.07909',
              },
              {
                ref: 'Loshchilov, I., Hutter, F. (2016). SGDR: Stochastic Gradient Descent with Warm Restarts.',
                url: 'https://arxiv.org/abs/1608.03983',
              },
            ].map((r, i) => (
              <div key={i} className="flex gap-4 items-start">
                <span className="flex-shrink-0 text-xs text-white/20 font-mono pt-0.5">
                  [{i + 1}]
                </span>
                <p className="text-sm text-white/40 leading-relaxed">
                  {r.ref} <ExtLink href={r.url}>arXiv</ExtLink>
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
