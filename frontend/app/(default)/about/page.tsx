import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'About - AI Melody Generator',
  description: 'Technical deep-dive into the AI Melody Generator: architecture, model evolution, and training methodology.',
};

export default function About() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section className="relative min-h-[60vh] flex items-end overflow-hidden pb-20 px-6 sm:px-10">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-1/4 w-[500px] h-[500px] rounded-full bg-indigo-600/20 blur-[120px]" />
          <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-fuchsia-600/15 blur-[100px]" />
        </div>
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />

        <div className="relative z-10 max-w-5xl mx-auto w-full">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-300/80 mb-6">Deep Dive</p>
          <h1 className="text-[clamp(2.5rem,6vw,5.5rem)] font-bold leading-[0.9] tracking-tight mb-6">
            Eight models,
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              34 million
            </span>
            <br />
            parameters
          </h1>
          <p className="text-xl text-white/50 max-w-2xl font-light leading-relaxed">
            An exploration of neural sequence generation applied to symbolic music &mdash; evolving over the past few years from simple LSTM baselines to a Transformer architecture with BPE tokenisation.
          </p>
        </div>
      </section>

      {/* ─── PULL QUOTE ─── */}
      <section className="border-t border-white/[0.06] py-16 px-6 sm:px-10">
        <div className="max-w-4xl mx-auto text-center">
          <blockquote className="text-2xl sm:text-3xl font-light leading-relaxed text-white/60 italic">
            &ldquo;Most research exists as static papers with cherry-picked audio samples. The goal here was to build a live, interactive system where each technique can be tested and compared in real time.&rdquo;
          </blockquote>
        </div>
      </section>

      {/* ─── MOTIVATION ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-12 gap-12">
          <div className="sm:col-span-4">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Why</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Symbolic,
              <br />not audio
            </h2>
          </div>
          <div className="sm:col-span-8 space-y-6 text-white/50 text-lg font-light leading-relaxed">
            <p>
              Consumer AI music tools generate audio directly from text prompts. This project works at a different level: generating symbolic MIDI sequences that musicians can edit, transpose, and arrange in a DAW. Individual notes, timing, velocity &mdash; preserved in a format that&apos;s both human-readable and machine-processable.
            </p>
            <p>
              Built on research from the{' '}
              <ExtLink href="https://arxiv.org/abs/1809.04281">Music Transformer</ExtLink> (Huang et al., 2019),
              the <ExtLink href="https://arxiv.org/abs/2002.00212">Pop Music Transformer</ExtLink> (Huang &amp; Yang, 2020) which introduced REMI tokenisation,
              and <ExtLink href="https://arxiv.org/abs/2301.11975">Fradet et al. (2023)</ExtLink> on BPE compression for symbolic music.
              V8 trains on the <ExtLink href="https://arxiv.org/abs/1810.12247">MAESTRO dataset</ExtLink> &mdash; 1,276 competition piano performances.
            </p>
          </div>
        </div>
      </section>

      {/* ─── TOKENISATION ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute top-0 left-0 w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[120px]" />

        <div className="relative max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4">Representation</p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            How music
            <br />
            <span className="text-white/40">becomes tokens</span>
          </h2>
          <p className="text-white/50 max-w-xl text-lg font-light mb-16">
            The single biggest impact on generation quality. Three strategies, each building on the last.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-white/[0.06] rounded-xl overflow-hidden">
            {[
              { era: 'V2\u2013V5', name: 'Pitch Strings', tokens: '59\u20131,279', desc: 'Raw pitch names and chord integers. No timing, no velocity. The model learns temporal structure purely from position.' },
              { era: 'V6', name: 'REMI', tokens: '362', desc: 'Typed tokens: Position, Pitch, Velocity, Duration, Tempo, Chord, Rest. Explicit musical structure. Vocabulary dropped despite encoding more.' },
              { era: 'V7\u2013V8', name: 'REMI + BPE', tokens: '512\u20131,024', desc: 'Byte Pair Encoding compresses multi-token note events into single merged tokens. More musical context per window.' },
            ].map((t) => (
              <div key={t.name} className="p-8 bg-white/[0.02]">
                <span className="text-xs text-indigo-400 font-mono mb-4 block">{t.era}</span>
                <h3 className="text-xl font-bold mb-2">{t.name}</h3>
                <p className="text-sm text-white/40 leading-relaxed mb-6">{t.desc}</p>
                <p className="text-3xl font-bold bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent font-mono">{t.tokens}</p>
                <p className="text-xs text-white/30 mt-1">tokens</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── TRANSFORMER ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-12">
            <div className="sm:col-span-5">
              <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Architecture</p>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight mb-4">
                LLaMA-style
                <br />Transformer
              </h2>
              <p className="text-white/50 font-light text-lg leading-relaxed">
                8 layers. 8 attention heads. 512 dimensions. Causal masking. Weight-tied embeddings. ~34M parameters.
              </p>
            </div>
            <div className="sm:col-span-7 grid grid-cols-2 gap-4">
              {[
                { name: 'RoPE', desc: 'Rotary positional encoding. Encodes position by rotating query/key vectors. Naturally decays attention with distance.' },
                { name: 'SwiGLU', desc: 'Gated feed-forward: W\u2082(SiLU(xW\u2081) \u2299 xW\u2083). Three projections give finer control over information flow.' },
                { name: 'RMSNorm', desc: 'Pre-norm without mean centering. Simpler than LayerNorm, empirically as effective for Transformer training.' },
                { name: 'Weight Tying', desc: 'Input embeddings and output projection share weights. Fewer parameters, built-in regularisation.' },
              ].map((item) => (
                <div key={item.name} className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.08]">
                  <h3 className="text-sm font-bold mb-2 font-mono">{item.name}</h3>
                  <p className="text-xs text-white/40 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── TRAINING ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] rounded-full bg-indigo-600/10 blur-[120px]" />

        <div className="relative max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4">Training</p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-16">
            How the models
            <br />
            <span className="text-white/40">learn to compose</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-white/[0.06] rounded-xl overflow-hidden">
            {[
              { name: 'Data Pipeline', desc: 'MIDI files split into train/val before augmentation to prevent leakage. Pitch shifting (\u00B16 semitones) triples effective dataset size.' },
              { name: 'Sequence Prep', desc: 'Sliding window over token sequences. Sequence length 256 for Transformer (512 max context at inference), 100 for LSTM. Configurable stride controls overlap.' },
              { name: 'Optimiser', desc: 'AdamW with cosine annealing (LSTM) or linear warmup + cosine decay (Transformer). Gradient clipping at norm 1.0.' },
              { name: 'Early Stopping', desc: 'Best checkpoint saved by validation loss. Training halts after 10\u201315 epochs without improvement. V7 stopped at epoch 45, V8 ran all 100.' },
            ].map((item) => (
              <div key={item.name} className="p-8 bg-white/[0.02]">
                <h3 className="font-bold mb-2">{item.name}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── SAMPLING ─── */}
      <section className="py-24 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-12 gap-12">
          <div className="sm:col-span-4">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Inference</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
              Controlling
              <br />randomness
            </h2>
          </div>
          <div className="sm:col-span-8">
            <div className="space-y-8">
              {[
                { name: 'Temperature', range: '0.1 \u2013 2.0', dflt: '0.8', desc: 'Divides logits before softmax. Below 1.0 sharpens the distribution (safer, more predictable). Above 1.0 flattens it (more surprising, more diverse).' },
                { name: 'Top-K', range: '0 \u2013 500', dflt: '50', desc: 'Keeps only the k highest-probability tokens. Everything else goes to negative infinity. Prevents sampling from the incoherent long tail.' },
                { name: 'Top-P (Nucleus)', range: '0.1 \u2013 1.0', dflt: '0.95', desc: 'Includes tokens until cumulative probability exceeds p. Adapts dynamically: fewer candidates when confident, more when uncertain.' },
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
          </div>
        </div>
      </section>

      {/* ─── OBSERVATIONS ─── */}
      <section className="border-t border-white/[0.06] bg-white/[0.02] py-20 px-6 sm:px-10">
        <div className="max-w-3xl mx-auto space-y-8">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-8 font-medium">Key Insights</p>
          {[
            { bold: 'Same architecture, different data, different vocabularies.', rest: 'V2\u2013V4 share identical LSTM configs but vocabulary ranged from 59 to 1,279 tokens. Jazz chord voicings alone drove a 21x increase over R&B.' },
            { bold: 'Tokenisation changed more than widening the network.', rest: 'V5 widened to [512, 512, 512] but kept raw encoding. V6 switched to REMI and the vocabulary dropped from 629 to 362 while encoding timing, velocity, and dynamics.' },
            { bold: 'V7 and V8 share the same architecture', rest: 'but differ in scale: V8 doubled BPE vocabulary to 1,024 and trained on 6x more data. V7 early-stopped at epoch 45 with val loss 0.095; V8 ran all 100 epochs.' },
          ].map((o, i) => (
            <div key={i} className="flex gap-6 items-start">
              <span className="flex-shrink-0 text-4xl font-bold text-indigo-500/20 leading-none font-mono">{String(i + 1).padStart(2, '0')}</span>
              <p className="text-white/50 leading-relaxed">
                <strong className="text-white/90">{o.bold}</strong>{' '}{o.rest}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="relative py-24 px-6 sm:px-10 border-t border-white/[0.06] overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-indigo-600/15 blur-[120px]" />
        </div>

        <div className="relative z-10 max-w-2xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Try it yourself
          </h2>
          <p className="text-white/50 text-lg font-light mb-8">
            Generate a melody, or explore the full source on GitHub.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-white text-[#07060b] font-semibold text-sm hover:bg-white/90 transition-colors"
            >
              Open Studio
            </Link>
            <a
              href="https://github.com/niallone/melodygenerator"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-8 py-3 rounded-lg border border-white/20 text-white font-semibold text-sm hover:bg-white/10 transition-colors"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>
    </>
  );
}

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 hover:underline transition-colors">
      {children}
    </a>
  );
}
