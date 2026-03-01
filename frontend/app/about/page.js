export const metadata = {
  title: 'About - AI Melody Generator',
  description: 'Technical deep-dive into the AI Melody Generator: architecture, model evolution, and training methodology.',
};

export default function About() {
  return (
    <article className="max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">About This Project</h1>
      <p className="text-dark-gray mb-8">
        An exploration of neural sequence generation applied to symbolic music, progressing from simple LSTM baselines to Transformer architectures with learned tokenisation.
      </p>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Motivation</h2>
        <p>
          Consumer AI music tools (Suno, Udio, Google&apos;s MusicLM) generate audio directly from text prompts. This project works at a different level of abstraction: generating symbolic MIDI sequences that musicians can edit, transpose, and arrange in a DAW. The distinction matters because symbolic representations preserve musical structure (individual notes, timing, velocity) in a format that&apos;s both human-readable and machine-processable.
        </p>
        <p className="mt-3">
          This approach builds on a line of research into symbolic music generation with neural networks. The{' '}
          <a href="https://arxiv.org/abs/1809.04281" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Music Transformer</a>{' '}
          (Huang et al., ICLR 2019) demonstrated that self-attention could capture long-range structure in piano performances. The{' '}
          <a href="https://arxiv.org/abs/2002.00212" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Pop Music Transformer</a>{' '}
          (Huang &amp; Yang, ACM MM 2020) introduced the REMI tokenisation scheme used in this project, showing that encoding beat-relative timing explicitly improves rhythmic coherence.{' '}
          <a href="https://arxiv.org/abs/2301.11975" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Fradet et al. (EMNLP 2023)</a>{' '}
          then showed that applying Byte Pair Encoding to symbolic music tokens reduces sequence length while improving generation quality, an approach implemented in the{' '}
          <a href="https://github.com/Natooz/MidiTok" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">MidiTok</a>{' '}
          library that this project uses. The V8 model also trains on the{' '}
          <a href="https://arxiv.org/abs/1810.12247" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">MAESTRO dataset</a>{' '}
          (Hawthorne et al., ICLR 2019), a standard benchmark of 1,276 competition piano performances with aligned MIDI.
        </p>
        <p className="mt-3">
          Most of this research exists as static papers with cherry-picked audio samples. The goal here was to bridge the gap between research and engineering: build a live, interactive system where each technique can be tested, compared, and tuned in real time. Rather than a paper that claims results, this is a working implementation that demonstrates them. The full pipeline (data processing, tokenisation, model training, inference API, and interactive frontend) ships as a single deployable stack, progressing from basic LSTMs with raw pitch encoding through to LLaMA-style Transformers with BPE tokenisation across seven model versions.
        </p>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Architecture</h2>
        <p>
          The system is a three-tier stack: a <strong>Next.js</strong> frontend with an in-browser MIDI player and Web Audio synthesiser, a <strong>FastAPI</strong> backend serving PyTorch models for real-time inference, and <strong>PostgreSQL</strong> for generation history and metadata. The frontend communicates with the API to request melody generation with configurable parameters (model selection, temperature, sequence length), then renders and plays the resulting MIDI in-browser.
        </p>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Model Evolution</h2>
        <p className="mb-4">
          Seven model versions track the progression from naive baselines to production-quality generation:
        </p>

        <div className="space-y-6">
          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V2: LSTM Baseline <span className="text-sm font-normal text-dark-gray">(11MB, 59 tokens)</span></h3>
            <p className="mt-1">
              Three-layer LSTM ([256, 512, 256] units) trained on 24 R&B and 90s hip-hop MIDI files with pitch transposition augmentation (~3x effective data). Character-level pitch encoding with fixed vocabulary. The small, genre-focused dataset produced a tight token distribution (59 unique tokens).
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V3: Genre Scaling <span className="text-sm font-normal text-dark-gray">(11MB, 635 tokens)</span></h3>
            <p className="mt-1">
              Same LSTM architecture and augmentation pipeline, scaled to ~180 dance/electronic tracks. The vocabulary jumped to 635 tokens due to the more harmonically complex source material, with the same model capacity as V2.
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V4: Jazz Corpus <span className="text-sm font-normal text-dark-gray">(12MB, 1,279 tokens)</span></h3>
            <p className="mt-1">
              ~120 jazz standards with augmentation. Vocabulary exploded to 1,279 tokens due to complex chord voicings: chords are encoded as dot-joined normalOrder integers (e.g. &quot;0.4.7&quot; for a major triad), and jazz voicings with extensions and alterations created a long tail of rare token combinations.
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V5: Mixed Genre, Wider Network <span className="text-sm font-normal text-dark-gray">(22MB, 629 tokens)</span></h3>
            <p className="mt-1">
              ~275 songs across genres with augmentation. Widened all LSTM layers to 512 units ([512, 512, 512], up from [256, 512, 256] in V2-V4). Added temperature-controlled sampling for generation diversity.
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V6: REMI Tokenisation <span className="text-sm font-normal text-dark-gray">(23MB, 362 tokens)</span></h3>
            <p className="mt-1">
              Same 275-song dataset as V5 but without augmentation. Switched from raw pitch encoding to <strong>REMI</strong> (REvamped MIDI-derived) tokenisation via MidiTok, and added a learned embedding layer (dim 128). REMI encodes note onset, duration, velocity, and tempo as discrete tokens, giving the model explicit timing information instead of forcing it to learn temporal structure implicitly. Vocabulary dropped from 629 to 362 despite the richer representation. Trained for 91 epochs on an H100 before early stopping (best val loss: 0.349).
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V7: Transformer <span className="text-sm font-normal text-dark-gray">(130MB, 512 tokens)</span></h3>
            <p className="mt-1">
              Replaced the LSTM with a LLaMA-style Transformer decoder: 8 layers, 8 attention heads, d_model=512, SwiGLU feed-forward (d_ff=2048), RoPE positional encoding, and RMSNorm. Multi-head self-attention allows the model to capture long-range dependencies across the full 512-token context window. Uses REMI tokenisation with BPE (vocab 512) on the same 275-song dataset. Trained for 45 epochs on an H100 before early stopping (best val loss: 0.095).
            </p>
          </div>

          <div className="border-l-4 border-primary pl-4">
            <h3 className="font-semibold text-lg">V8: BPE Tokenisation <span className="text-sm font-normal text-dark-gray">(131MB, 1,024 tokens)</span></h3>
            <p className="mt-1">
              Same LLaMA-style Transformer as V7, trained on a significantly larger dataset: 1,551 MIDI files combining the original 275 mixed-genre songs with 1,276 performances from the <strong>MAESTRO</strong> dataset (classical piano competition recordings from the International Piano-e-Competition). BPE vocabulary doubled to 1,024 to handle the richer data. Trained for the full 100 epochs on an H100 without early stopping (best val loss: 0.920, higher than V7 due to the larger vocabulary and more diverse data).
            </p>
          </div>
        </div>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Observations</h2>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Same architecture, different data, different vocabularies.</strong> V2, V3, and V4 share identical LSTM configs ([256, 512, 256]) but vocabulary ranged from 59 to 1,279 tokens depending on genre complexity. Jazz chord voicings alone drove a 21x vocab increase over R&B.</li>
          <li><strong>Tokenisation changed more than widening the network.</strong> V5 widened to [512, 512, 512] but kept raw pitch encoding (629 tokens). V6 kept the same layer width, switched to REMI tokenisation, and the vocabulary dropped to 362 while encoding timing, velocity, and dynamics that raw pitch encoding discards.</li>
          <li><strong>V7 and V8 share the same Transformer config</strong> (8 layers, 8 heads, 512 dims, RoPE, SwiGLU, RMSNorm, weight-tied embeddings) but differ in two ways: V8 doubled the BPE vocabulary from 512 to 1,024 and trained on 6x more data (1,551 files vs 275). V7 early-stopped at epoch 45 with val loss 0.095; V8 ran all 100 epochs with val loss 0.920. The losses aren&apos;t directly comparable due to different vocabularies and data distributions.</li>
        </ul>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Stack</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold mb-1">Frontend</h3>
            <p className="text-sm">Next.js 15, React, Web Audio API, Tailwind CSS</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Backend</h3>
            <p className="text-sm">Python, FastAPI, PyTorch, MidiTok</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Training</h3>
            <p className="text-sm">PyTorch, music21, MidiTok, NVIDIA H100 80GB</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Infrastructure</h3>
            <p className="text-sm">Docker Compose, PostgreSQL, Traefik, GitHub Actions</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4">Source</h2>
        <p>
          The full source, including the frontend, backend, model training pipeline, and all seven model checkpoints, is available on{' '}
          <a
            href="https://github.com/niallone/melodygenerator"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline font-medium"
          >
            GitHub
          </a>.
        </p>
      </section>
    </article>
  );
}
