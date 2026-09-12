import { useEffect, useRef, useState } from "react";
import { Application } from "@splinetool/runtime";

export function SplineLoadingScreen() {
  const archetypes = [
    { label: "SS", src: "/ss.webp" },
    { label: "PP", src: "/pp.avif" },
    { label: "MM", src: "/mm.jpg" },
    { label: "BB", src: "/bb.jpg" },
    { label: "DD", src: "/dd.jpg" },
  ];
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [archetypeIndex, setArchetypeIndex] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const archetypeTimer = window.setInterval(() => {
      setArchetypeIndex((current) => (current + 1) % archetypes.length);
    }, 900);

    return () => window.clearInterval(archetypeTimer);
  }, [archetypes.length]);

  useEffect(() => {
    let cancelled = false;
    let progressTimer: number | undefined;
    let readyTimer: number | undefined;
    let splineApp: Application | null = null;

    const preloadSpline = async () => {
      progressTimer = window.setInterval(() => {
        setProgress((current) => Math.min(current + 8, 88));
      }, 100);

      try {
        const canvas = canvasRef.current;
        if (!canvas) throw new Error("Spline preload canvas is unavailable");

        if (canvas.clientWidth > 0 && canvas.clientHeight > 0) {
          splineApp = new Application(canvas);
          await splineApp.load("/gradient.splinecode");
        }
      } catch (error) {
        console.warn("Spline runtime preload failed; continuing with the visual fallback:", error);
      } finally {
        if (progressTimer) window.clearInterval(progressTimer);
        if (!cancelled) {
          setProgress(100);
          readyTimer = window.setTimeout(() => setReady(true), 350);
        }
      }
    };

    void preloadSpline();
    return () => {
      cancelled = true;
      if (progressTimer) window.clearInterval(progressTimer);
      if (readyTimer) window.clearTimeout(readyTimer);
      if (splineApp) splineApp.dispose();
    };
  }, []);

  if (ready) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden bg-[#e8dfcf] text-forest">
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full opacity-0 pointer-events-none" aria-hidden="true" />
      <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(#45604e_0.7px,transparent_0.7px)] [background-size:18px_18px]" />
      <div className="relative flex w-full max-w-md flex-col items-center px-8 text-center">
        <div className="mb-10 flex h-32 w-52 flex-col items-center justify-end gap-2" aria-hidden="true">
          <img
            key={archetypes[archetypeIndex].label}
            src={archetypes[archetypeIndex].src}
            alt=""
            className="animate-stone-rise h-24 w-full object-contain"
          />
          <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-forest/55">
            {archetypes[archetypeIndex].label}
          </span>
        </div>
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-clay">Sahayak</p>
        <h1 className="mt-3 font-display text-4xl">Finding your inner calm</h1>
        <div className="mt-8 h-1.5 w-64 overflow-hidden rounded-full bg-forest/15">
          <div
            className="h-full rounded-full bg-clay transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="mt-3 font-mono text-[10px] tracking-[0.2em] text-forest/55">
          {progress}%
        </span>
      </div>
    </div>
  );
}
