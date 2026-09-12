import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getDecisionTrace, subscribeToStore } from "@/lib/store";
import {
  ArrowLeft,
  ShieldCheck,
  Layers,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";

export const Route = createFileRoute("/counsellor/trace/$threadId")({
  head: () => ({
    meta: [{ title: "AI Decision Trace — Sahayak" }],
  }),
  component: TraceViewPage,
});

export default function TraceViewPage() {
  const { threadId } = Route.useParams();
  const [trace, setTrace] = useState(() => getDecisionTrace(threadId));

  useEffect(() => {
    const refresh = () => setTrace(getDecisionTrace(threadId));
    refresh();
    const unsubscribe = subscribeToStore(refresh);
    return () => unsubscribe();
  }, [threadId]);

  const routeColor =
    trace.decision.route === "crisis"
      ? { text: "text-red-700", bg: "bg-red-500/15 border-red-400/30", badge: "bg-red-600 text-white" }
      : trace.decision.route === "escalate"
      ? { text: "text-clay", bg: "bg-clay/10 border-clay/30", badge: "bg-clay text-white" }
      : { text: "text-forest", bg: "bg-forest/10 border-forest/30", badge: "bg-forest text-forest-foreground" };

  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-3xl space-y-8">
        {/* Header */}
        <div className="border-b border-foreground/10 pb-6 space-y-3">
          <Link
            to="/counsellor/alerts"
            className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Alert Queue</span>
          </Link>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-clay">
            <Layers className="h-4 w-4" />
            <span>Explainable AI Audit Trail</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-display">Decision Trace</h1>
          <div className="flex flex-wrap gap-3 text-xs text-foreground/60 font-mono">
            <span>Thread: {trace.thread_id}</span>
            <span>·</span>
            <span>Case: {trace.case_id}</span>
            <span>·</span>
            <span>Policy: {trace.decision.policy_version}</span>
          </div>
        </div>

        {/* Primary Decision Card */}
        <div className={`rounded-3xl border p-6 md:p-8 space-y-4 shadow-[var(--shadow-lift)] ${routeColor.bg}`}>
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-[10px] font-medium uppercase tracking-widest text-foreground/50 block mb-1">
                System Decision
              </span>
              <span className={`font-display text-4xl font-bold ${routeColor.text}`}>
                {trace.decision.route.toUpperCase()}
              </span>
            </div>
            <span className={`rounded-full px-4 py-2 text-xs font-bold uppercase tracking-wider shadow-sm ${routeColor.badge}`}>
              Route Confirmed
            </span>
          </div>
          <p className="text-xs text-foreground/60 font-mono">
            Policy version <strong>{trace.decision.policy_version}</strong> · Human counsellor
            override applies at all times
          </p>
        </div>

        {/* Why — Structured Reasons */}
        <div className="rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-4 shadow-[var(--shadow-soft)]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-sage-deep" />
            <span className="text-sm font-semibold text-foreground uppercase tracking-wider">
              Explanation — Why this route was chosen
            </span>
          </div>
          <ul className="space-y-3">
            {trace.decision.reasons.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-xl bg-background/50 border border-foreground/5 p-3.5"
              >
                <ChevronRight className="h-4 w-4 text-clay mt-0.5 flex-shrink-0" />
                <span className="text-sm text-foreground/85 leading-relaxed">{r}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Fusion Confidence Visualization */}
        <div className="rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-5 shadow-[var(--shadow-soft)]">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm font-semibold uppercase tracking-wider text-foreground">
              Multi-Signal Fusion Confidence
            </span>
            <span className="font-display text-3xl font-bold text-clay">
              {(trace.fusion.confidence * 100).toFixed(0)}%
            </span>
          </div>

          {/* Confidence Bar */}
          <div className="space-y-2">
            <div className="h-3 w-full rounded-full bg-foreground/10 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-clay/80 to-clay rounded-full transition-all duration-700"
                style={{ width: `${trace.fusion.confidence * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-foreground/40 uppercase font-mono tracking-widest">
              <span>Low certainty</span>
              <span>High certainty</span>
            </div>
          </div>

          {/* Top Signals Breakdown */}
          <div className="space-y-2">
            <span className="text-xs text-foreground/50 uppercase tracking-wider block font-medium">
              Top Contributing Signals
            </span>
            <div className="flex flex-wrap gap-2">
              {trace.fusion.top_signals.map((sig) => {
                const [name, scoreStr] = sig.replace(")", "").split("(");
                const score = parseFloat(scoreStr || "0.8");
                return (
                  <div
                    key={sig}
                    className="flex items-center gap-2 rounded-full border border-foreground/10 bg-background/60 px-3 py-1.5"
                  >
                    <span className="text-xs font-mono text-foreground/80">{name.trim()}</span>
                    <div className="h-1.5 w-14 rounded-full bg-foreground/10 overflow-hidden">
                      <div
                        className="h-full bg-forest rounded-full"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-mono text-clay font-semibold">
                      {(score * 100).toFixed(0)}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Degraded Mode Warnings */}
        {trace.errors.length > 0 && (
          <div className="rounded-3xl border border-clay/30 bg-clay/5 p-6 space-y-3">
            <div className="flex items-center gap-2 text-clay">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-semibold uppercase tracking-wider">
                Degraded Mode — Signal Gaps
              </span>
            </div>
            <p className="text-xs text-foreground/65">
              Some telemetry services were unavailable when this decision was computed. The system
              continued in graceful degraded mode. Confidence adjusted accordingly.
            </p>
            <ul className="space-y-1">
              {trace.errors.map((err, i) => (
                <li key={i} className="text-xs text-clay/90 font-mono flex items-start gap-2">
                  <span>⚠</span>
                  <span>{err}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Counsellor Override Section */}
        <div className="rounded-3xl border border-forest/20 bg-forest/5 p-6 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-forest" />
            <span className="text-sm font-semibold text-forest uppercase tracking-wider">
              Counsellor Authority Override
            </span>
          </div>
          <p className="text-xs text-foreground/70 leading-relaxed">
            The AI decision above is advisory only. As an assigned counsellor, your clinical
            judgment overrides the system at all times. You can approve, de-escalate, or route this
            case independently from the Alert Queue.
          </p>
          <div className="flex gap-3 pt-2">
            <Link
              to="/counsellor/alerts"
              className="rounded-full bg-forest px-5 py-2 text-xs font-medium text-forest-foreground hover:bg-clay transition-colors"
            >
              Return to Triage Queue
            </Link>
            <Link
              to="/counsellor"
              className="rounded-full border border-foreground/20 px-5 py-2 text-xs font-medium text-foreground hover:bg-card transition-colors"
            >
              Open Case Dossier
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
