import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getAlerts, decideAlert, subscribeToStore, TriageAlert } from "@/lib/store";
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Layers,
  ShieldAlert,
  ArrowRight,
  Filter,
  MessageSquare,
  EyeOff,
  Lock,
} from "lucide-react";

export const Route = createFileRoute("/counsellor/alerts")({
  head: () => ({
    meta: [{ title: "Triage Alert Queue — Sahayak" }],
  }),
  component: AlertQueuePage,
});

export default function AlertQueuePage() {
  const [alerts, setAlerts] = useState<TriageAlert[]>([]);
  const [selectedRisk, setSelectedRisk] = useState<string>("ALL");

  useEffect(() => {
    const refresh = () => setAlerts(getAlerts());
    refresh();
    const unsubscribe = subscribeToStore(refresh);
    return () => unsubscribe();
  }, []);

  const handleDecision = (alertId: string, approved: boolean) => {
    decideAlert(alertId, approved);
    setAlerts(getAlerts());
  };

  const filteredAlerts =
    selectedRisk === "ALL" ? alerts : alerts.filter((a) => a.risk_level === selectedRisk);

  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-foreground/10 pb-6">
          <div className="space-y-1">
            <Link
              to="/counsellor"
              className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors mb-2"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Field Office</span>
            </Link>
            <h1 className="text-4xl md:text-5xl font-display">Triage Alert Queue</h1>
            <p className="text-sm text-foreground/60">
              Human-in-the-loop escalation gates with explainable score confidence.
            </p>
          </div>

          {/* Risk Filters */}
          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-card p-1 rounded-full border border-foreground/10">
            {["ALL", "CRITICAL", "HIGH", "MODERATE"].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setSelectedRisk(r)}
                className={`rounded-full px-3 py-1 text-[11px] font-medium transition-all ${
                  selectedRisk === r
                    ? "bg-forest text-forest-foreground shadow-sm font-semibold"
                    : "text-foreground/60 hover:text-foreground"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-foreground/20 p-12 text-center text-foreground/50">
              No alerts matching this filter.
            </div>
          ) : (
            filteredAlerts.map((a) => {
              const isCritical = a.risk_level === "CRITICAL";
              const isHigh = a.risk_level === "HIGH";

              return (
                <div
                  key={a.alert_id}
                  className={`rounded-3xl border p-6 transition-all space-y-5 ${
                    isCritical
                      ? "border-red-500/40 bg-card shadow-[var(--shadow-lift)] ring-1 ring-red-500/20"
                      : isHigh
                      ? "border-clay/40 bg-card"
                      : "border-foreground/10 bg-card/60"
                  }`}
                >
                  {/* Top Bar */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-bold tracking-wider uppercase ${
                          isCritical
                            ? "bg-red-500/20 text-red-700"
                            : isHigh
                            ? "bg-clay/20 text-clay"
                            : "bg-sage/40 text-sage-deep"
                        }`}
                      >
                        {a.risk_level}
                      </span>
                      <span className="font-mono text-sm font-semibold text-foreground">
                        {a.alert_id}
                      </span>
                      <span className="text-xs text-foreground/45">· {a.raised_at}</span>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-mono text-foreground/70">
                      <span>
                        Composite: <strong className="text-foreground">{(a.composite_score * 100).toFixed(0)}%</strong>
                      </span>
                      <span>
                        Confidence: <strong className="text-foreground">{(a.confidence * 100).toFixed(0)}%</strong>
                      </span>
                      <span>
                        Priority Score: <strong className="text-clay">{a.triage_priority_score}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Victim Privacy & Identity Status */}
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-background/60 p-3 border border-foreground/10 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-foreground">
                        Victim Codeword: {a.victim_info?.codeword || a.case_id}
                      </span>
                      {a.victim_info?.share_personal_info ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Personal Info Disclosed</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-foreground/10 border border-foreground/15 px-2.5 py-0.5 text-[11px] font-semibold text-foreground/70">
                          <Lock className="h-3 w-3 text-foreground/60" />
                          <span>Strict Anonymous Shield</span>
                        </span>
                      )}
                    </div>
                    {a.victim_info?.share_personal_info && (
                      <div className="text-[11px] text-foreground/75 font-medium">
                        {a.victim_info.name && <span>{a.victim_info.name}</span>}
                        {a.victim_info.email && <span> · {a.victim_info.email}</span>}
                      </div>
                    )}
                    {a.victim_info?.latest_mood && (
                      <div className="text-[11px] text-foreground/60 font-mono">
                        Intake Mood: <span className="text-clay font-bold">{a.victim_info.latest_mood}</span>
                        {a.victim_info.latest_sleep && ` · Rest: ${a.victim_info.latest_sleep}`}
                      </div>
                    )}
                  </div>

                  {/* Text from Victim (Live Input Trigger) */}
                  {a.victim_text && (
                    <div className="rounded-2xl bg-background/80 p-4 border border-foreground/10 space-y-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-clay flex items-center gap-1.5">
                        <MessageSquare className="h-3.5 w-3.5" /> Triggering Text Received From Victim
                      </span>
                      <p className="text-xs text-foreground/90 italic font-mono bg-card/70 p-3 rounded-xl border border-foreground/5 leading-relaxed">
                        {a.victim_info?.share_personal_info === false
                          ? "[Confidential sanctuary chat message shielded by victim choice]"
                          : `"${a.victim_text}"`}
                      </p>
                    </div>
                  )}

                  {/* Multi-turn Interaction History leading to Alert */}
                  {a.history && a.history.length > 0 && (
                    <div className="rounded-2xl bg-background/50 p-4 border border-foreground/5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground/50 block">
                          Victim Interaction History Timeline ({a.history.length} events leading to alert)
                        </span>
                        <span className="text-[10px] font-mono text-foreground/40">Chronological Telemetry</span>
                      </div>
                      <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                        {a.history.map((h, hIdx) => (
                          <div
                            key={h.id || hIdx}
                            className="bg-card/80 p-2.5 rounded-xl border border-foreground/5 text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between text-[10px] font-mono text-foreground/45">
                              <span className="font-semibold text-clay uppercase">
                                {h.source === "chat" ? "Sanctuary Chat" : h.source === "questionnaire" ? "Check-in" : "Intake"}
                              </span>
                              <span>{h.timestamp}</span>
                            </div>
                            <p className="text-foreground/80 italic font-mono text-[11px]">
                              {a.victim_info?.share_personal_info === false && h.source === "chat"
                                ? "[Confidential chat message shielded]"
                                : `"${h.text}"`}
                            </p>
                            {h.details && (
                              <div className="text-[10px] text-foreground/50 font-mono">{h.details}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reasons Triggered */}
                  <div className="rounded-2xl bg-background/50 p-4 border border-foreground/5 space-y-2">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground/50 block">
                      Trigger Reasons (Rule & Model Fusion)
                    </span>
                    <ul className="space-y-1 text-xs text-foreground/80">
                      {a.reasons.map((r, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-clay mt-0.5 font-bold">→</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Actions & Decision Status */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
                    <Link
                      to="/counsellor/trace/$threadId"
                      params={{ threadId: a.thread_id }}
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-clay hover:underline self-start"
                    >
                      <Layers className="h-3.5 w-3.5" />
                      <span>Inspect Explainable AI Decision Trace</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>

                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      {a.decision_status === "pending" ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleDecision(a.alert_id, true)}
                            className="inline-flex items-center gap-1.5 rounded-full bg-forest px-4 py-2 text-xs font-semibold text-forest-foreground hover:bg-clay transition-colors"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            <span>Approve Escalation</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDecision(a.alert_id, false)}
                            className="inline-flex items-center gap-1.5 rounded-full border border-foreground/20 px-4 py-2 text-xs font-medium text-foreground hover:bg-card transition-colors"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            <span>De-escalate</span>
                          </button>
                        </>
                      ) : (
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
                            a.decision_status === "approved"
                              ? "bg-green-600/15 text-green-800"
                              : "bg-foreground/10 text-foreground/60"
                          }`}
                        >
                          {a.decision_status === "approved"
                            ? "✓ Escalation Approved"
                            : "De-escalated by Counsellor"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
