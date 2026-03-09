'use client';

import { useState } from 'react';
import { MelodyGenerator } from '../../components/melody/melody-generator';
import { MelodyList } from '../../components/melody/melody-list';
import Gallery from '../../components/melody/gallery';
import Link from 'next/link';

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <>
      {/* ─── HERO ─── */}
      <section className="relative min-h-[70vh] flex items-center overflow-hidden px-6 sm:px-10">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-indigo-600/30 blur-[120px] animate-[drift_20s_ease-in-out_infinite]" />
          <div className="absolute -bottom-20 right-0 w-[600px] h-[600px] rounded-full bg-fuchsia-600/20 blur-[120px] animate-[drift_25s_ease-in-out_infinite_reverse]" />
        </div>
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />

        <div className="relative z-10 max-w-5xl mx-auto w-full">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-300/80 mb-8 font-light">Research Project</p>
          <h1 className="text-[clamp(2.5rem,7vw,6rem)] font-bold leading-[0.9] tracking-tight mb-8">
            AI Melody
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              Generator
            </span>
          </h1>
          <p className="text-xl text-white/50 max-w-lg font-light leading-relaxed mb-10">
            Exploring neural sequence generation applied to symbolic music &mdash; from LSTMs to Transformers across seven model versions.
          </p>
          <Link
            href="/about"
            className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
          >
            How it works
            <span className="text-lg">&rarr;</span>
          </Link>
        </div>
      </section>

      {/* ─── STUDIO ─── */}
      <section className="py-20 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Try it</p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-12">
            Generate a melody
          </h2>

          <div className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-6 sm:p-8">
            <MelodyGenerator onGenerated={() => setRefreshKey((k) => k + 1)} />
          </div>

          <div className="mt-8">
            <MelodyList />
          </div>
        </div>
      </section>

      {/* ─── GALLERY ─── */}
      <section className="py-20 px-6 sm:px-10 border-t border-white/[0.06]">
        <div className="max-w-[1400px] mx-auto">
          <div className="max-w-xl mb-12">
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-400/80 mb-4 font-medium">Gallery</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Recent generations
            </h2>
          </div>
          <Gallery refreshKey={refreshKey} />
        </div>
      </section>
    </>
  );
}
