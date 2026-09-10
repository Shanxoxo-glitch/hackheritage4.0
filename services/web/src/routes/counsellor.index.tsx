import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  getCases,
  updateCaseStatus,
  addCaseNote,
  CounsellorCase,
} from "@/lib/store";
import { TimelineOverlay } from "@/components/counsellor/TimelineOverlay";
import {
  Folder,
  FileText,
  Clock,
  HeartHandshake,
  CheckCircle2,
  AlertTriangle,
  Plus,
  Send,
  Layers,
  ArrowRight,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";

export const Route = createFileRoute("/counsellor/")({
  head: () => ({
    meta: [{ title: "Counsellor Field Office — Sahayak" }],
  }),
  component: CounsellorDashboardPage,
});

export default function CounsellorDashboardPage() {
  const [cases, setCases] = useState<CounsellorCase[]>([]);
  const [selectedCase, setSelectedCase] = useState<CounsellorCase | null>(null);
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    const list = getCases();
    setCases(list);
    if (list.length > 0) {
      setSelectedCase(list[0]);
    }
  }, []);

  const handleStatusChange = (status: CounsellorCase["status"]) => {
    if (!selectedCase) return;
    updateCaseStatus(selectedCase.id, status);
    const updated = getCases();
    setCases(updated);
    const refreshed = updated.find((c) => c.id === selectedCase.id);
    if (refreshed) setSelectedCase(refreshed);
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !newNote.trim()) return;
    addCaseNote(selectedCase.id, newNote);
    setNewNote("");
    const updated = getCases();
    setCases(updated);
    const refreshed = updated.find((c) => c.id === selectedCase.id);
    if (refreshed) setSelectedCase(refreshed);
  };

  const getStatusStep = (status: CounsellorCase["status"]) => {
    switch (status) {
      case "new":
        return 1;
      case "contacted":
        return 2;
      case "in_support":
        return 3;
      case "resolved":
        return 4;
      default:
        return 1;
    }
  };

  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Top Field Office Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-foreground/10 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-clay">
              <Stethoscope className="h-3.5 w-3.5" />
              <span>Counsellor Field Office · Dr. Ananya Roy</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-display">Assigned Case Records</h1>
            <p className="text-sm text-foreground/60">
              Tactile manila case files with timeline distress tracking and field clinical notes.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start sm:self-auto">
            <Link
              to="/counsellor/alerts"
              className="inline-flex items-center gap-2 rounded-full border border-clay bg-clay/10 px-5 py-2.5 text-xs font-semibold text-clay hover:bg-clay hover:text-white transition-colors"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Triage Alert Queue</span>
            </Link>
            <Link
              to="/counsellor/trace/$threadId"
              params={{ threadId: "thread-8492" }}
              className="inline-flex items-center gap-2 rounded-full bg-forest px-5 py-2.5 text-xs font-semibold text-forest-foreground hover:bg-clay transition-colors"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Inspect AI Trace</span>
            </Link>
          </div>
        </div>

        {/* Main Work Area: Case Cards Grid + Selected Case Notebook */}
        <div className="grid lg:grid-cols-12 gap-8">
          {/* Left Column: Paper File Case Cards */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-medium uppercase tracking-wider text-foreground/50">
                Assigned Dossiers ({cases.length})
              </span>
              <span className="text-[11px] text-foreground/40 font-mono">Confidentiality Scoped</span>
            </div>

            <div className="space-y-3">
              {cases.map((c) => {
                const isSelected = selectedCase?.id === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => setSelectedCase(c)}
                    className={`rounded-2xl border p-5 transition-all cursor-pointer relative overflow-hidden ${
                      isSelected
                        ? "border-clay bg-card shadow-[var(--shadow-lift)] ring-1 ring-clay/40"
                        : "border-foreground/10 bg-card/50 hover:bg-card hover:border-foreground/20"
                    }`}
                  >
                    {/* Paper file top tab effect */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2">
                        <Folder className={`h-4 w-4 ${isSelected ? "text-clay" : "text-foreground/40"}`} />
                        <span className="font-mono text-base font-bold text-foreground">
                          {c.codeword}
                        </span>
                      </div>
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                          c.triage_priority.startsWith("P1")
                            ? "bg-red-500/15 text-red-700"
                            : c.triage_priority.startsWith("P2")
                            ? "bg-clay/15 text-clay"
                            : "bg-sage/30 text-sage-deep"
                        }`}
                      >
                        {c.triage_priority}
                      </span>
                    </div>

                    <p className="text-xs text-foreground/70 line-clamp-2 leading-relaxed mb-3">
                      {c.summary}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-foreground/50 border-t border-foreground/10 pt-3">
                      <span>Status: <strong className="capitalize text-foreground/80">{c.status.replace("_", " ")}</strong></span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {c.last_interaction}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Active Dossier & Field Notebook */}
          <div className="lg:col-span-7">
            {selectedCase ? (
              <div className="rounded-3xl border border-foreground/15 bg-card p-6 md:p-8 space-y-8 shadow-[var(--shadow-soft)]">
                {/* Dossier Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-foreground/10 pb-5">
                  <div>
                    <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                      Active Victim Dossier
                    </span>
                    <h2 className="font-mono text-3xl font-bold text-foreground">
                      {selectedCase.codeword}
                    </h2>
                    <div className="text-xs text-foreground/50 mt-0.5">
                      Case ID: {selectedCase.case_id} · Began {selectedCase.created_at}
                    </div>
                  </div>

                  {/* Status Ribbon Selector */}
                  <div className="flex flex-wrap gap-1.5 self-start sm:self-auto bg-foreground/5 p-1 rounded-full border border-foreground/10">
                    {(["new", "contacted", "in_support", "resolved"] as const).map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => handleStatusChange(st)}
                        className={`rounded-full px-3 py-1 text-[11px] font-medium transition-all ${
                          selectedCase.status === st
                            ? "bg-forest text-forest-foreground shadow-sm font-semibold"
                            : "text-foreground/60 hover:text-foreground"
                        }`}
                      >
                        {st === "in_support" ? "In Support" : st.charAt(0).toUpperCase() + st.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* SHOWPIECE: Timeline Distress Overlay */}
                <div className="rounded-2xl border border-foreground/10 bg-background/50 p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-foreground/70">
                      Distress Trajectory & Clinical Milestones
                    </span>
                    <span className="text-[11px] text-foreground/45">Multi-signal fusion index</span>
                  </div>
                  <TimelineOverlay data={selectedCase.distress_trajectory} />
                </div>

                {/* Signals Tags */}
                <div>
                  <span className="text-xs text-foreground/50 uppercase tracking-wider block mb-2 font-medium">
                    Telemetry & Consent Indicators
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {selectedCase.signals.map((sig) => (
                      <span
                        key={sig}
                        className="rounded-full bg-sage/25 px-3 py-1 text-xs font-medium text-forest-deep"
                      >
                        ✓ {sig}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Field Notebook (Notes Editor) */}
                <div className="space-y-4 pt-2 border-t border-foreground/10">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-clay flex items-center gap-1.5">
                      <FileText className="h-4 w-4" /> Field Clinical Notebook
                    </span>
                    <span className="text-[10px] text-foreground/40 font-mono">
                      Timestamped Audit
                    </span>
                  </div>

                  {/* Add Note Form */}
                  <form onSubmit={handleAddNote} className="space-y-2">
                    <textarea
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      rows={3}
                      placeholder="Record clinical observation, grounding anchor applied, or callback notes..."
                      className="w-full rounded-2xl border border-foreground/15 bg-background/80 p-3.5 text-xs text-foreground placeholder:text-foreground/35 focus:border-clay focus:outline-none"
                    />
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={!newNote.trim()}
                        className="inline-flex items-center gap-2 rounded-full bg-clay px-5 py-2 text-xs font-medium text-white hover:bg-forest transition-colors disabled:opacity-40"
                      >
                        <Send className="h-3 w-3" />
                        <span>Log Note</span>
                      </button>
                    </div>
                  </form>

                  {/* Past Notes Stream */}
                  <div className="space-y-3 pt-2">
                    {selectedCase.fieldNotes.map((note) => (
                      <div
                        key={note.id}
                        className="rounded-2xl border border-foreground/10 bg-background/40 p-4 space-y-1.5 text-xs"
                      >
                        <div className="flex items-center justify-between text-[11px] text-foreground/50 border-b border-foreground/5 pb-1">
                          <strong className="text-foreground/80">{note.author}</strong>
                          <span className="font-mono">{note.timestamp}</span>
                        </div>
                        <p className="text-foreground/85 leading-relaxed pt-1">{note.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-foreground/20 p-16 text-center text-foreground/40">
                Select a case record to inspect field notes
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
