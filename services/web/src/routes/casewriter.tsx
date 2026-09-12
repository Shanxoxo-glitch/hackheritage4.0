import { useState, useRef, useEffect } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { streamChat, scoreTextLive } from "@/lib/api";
import {
  recordVictimInteraction,
  getCurrentUser,
  getActiveCodeword,
  logoutUser,
  addCaseNote,
  getCases,
  CounsellorCase,
} from "@/lib/store";
import {
  ArrowLeft,
  Send,
  Sparkles,
  Scale,
  Bot,
  FileText,
  CheckCircle2,
  Cpu,
  BookmarkPlus,
  Power,
  Folder,
  Layers,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

export const Route = createFileRoute("/casewriter")({
  head: () => ({
    meta: [{ title: "CaseWriter AI — Clinical & Legal Studio" }],
  }),
  component: CaseWriterPage,
});

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  source?: "vm_orchestrator" | "backend_casewriter_engine" | "local_fallback";
}

const CASEWRITER_WELCOME: Message = {
  role: "assistant",
  content:
    "⚖️ CaseWriter AI Initialized.\n\nConnected directly to live Azure VM Orchestrator (port :8500) and backend perception pipeline. Enter case observations, incident narratives, hearing details, or police report excerpts to generate structured risk classifications, key signals, and clinician-grounded recommendations.",
};

export default function CaseWriterPage() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const activeCodeword = currentUser?.codeword || getActiveCodeword() || "quiet-sanctuary";

  const [cases, setCases] = useState<CounsellorCase[]>([]);
  const [selectedCase, setSelectedCase] = useState<CounsellorCase | null>(null);

  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [CASEWRITER_WELCOME];
    try {
      const stored = localStorage.getItem(`casewriter_chat_messages_${activeCodeword}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return [CASEWRITER_WELCOME];
  });

  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [savedNotes, setSavedNotes] = useState<Record<number, boolean>>({});

  const abortRef = useRef<(() => void) | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const list = getCases();
    setCases(list);
    if (list.length > 0) setSelectedCase(list[0]);
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(`casewriter_chat_messages_${activeCodeword}`, JSON.stringify(messages));
      } catch {}
    }
  }, [messages, activeCodeword]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSaveToDossier = (text: string, index: number) => {
    const targetCaseId = selectedCase?.case_id || activeCodeword;
    addCaseNote(targetCaseId, `[CaseWriter Synthesis] ${text}`, "CaseWriter AI");
    setSavedNotes((prev) => ({ ...prev, [index]: true }));
  };

  const handleSend = (presetText?: string) => {
    const rawMsg = presetText || input;
    if (!rawMsg.trim() || streaming) return;
    const userMsg = rawMsg;
    setInput("");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "assistant", content: "" },
    ]);
    setStreaming(true);

    abortRef.current = streamChat(
      {
        case_id: selectedCase?.case_id || activeCodeword,
        channel: "pwa",
        message: userMsg,
        model: "casewriter",
      },
      (delta) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant") {
            return [...prev.slice(0, -1), { ...last, content: last.content + delta }];
          }
          return prev;
        });
      },
      (final) => {
        setStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              {
                ...last,
                content: final.reply || last.content,
                source: (final as any).source,
              },
            ];
          }
          return prev;
        });
      },
      (err) => {
        setStreaming(false);
        console.error("StreamChat error:", err);
      }
    );
  };

  const casewriterPresets = [
    {
      label: "🚨 Urgent Stalking & Abuse",
      prompt: "Victim reports spouse took house keys, confiscated phone, and issued direct physical threats.",
    },
    {
      label: "📋 Extract Risk & Recommended Action",
      prompt: "Analyze latest dialogue: feeling trapped and unable to sleep for 4 days. Synthesize CaseWriter action.",
    },
    {
      label: "⚖️ Legal & Protection Order Guidance",
      prompt: "What are the immediate steps under the Protection of Women from Domestic Violence Act for urgent relief?",
    },
    {
      label: "🍃 Grounding & Routine Cadence",
      prompt: "Victim completed morning sensory walk, reported feeling quiet and stable. Formulate 7-day monitoring brief.",
    },
  ];

  return (
    <div className="grain min-h-screen bg-background text-foreground flex flex-col justify-between relative overflow-hidden">
      {/* Top Bar */}
      <div className="sticky top-0 z-30 w-full border-b border-clay/20 bg-card/95 px-4 py-2.5 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="p-1 rounded-md bg-clay/10 text-clay">
              <Scale className="h-4 w-4" />
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-clay">
              CaseWriter AI · Clinical & Legal Decision Studio
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-clay/10 text-clay border border-clay/25 font-mono text-[11px] font-semibold">
              <Cpu className="h-3 w-3 animate-pulse text-clay" />
              <span>Azure VM (:8500) & Backend (:8400)</span>
            </span>
            <Link
              to="/chat"
              search={{ mode: "sahayak" }}
              className="inline-flex items-center gap-1.5 rounded-full bg-forest px-3.5 py-1 text-xs font-semibold text-white hover:!bg-clay transition-all"
            >
              <Bot className="h-3.5 w-3.5" />
              <span>Switch to Sahayak Mode</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Subheader */}
      <header className="mx-auto w-full max-w-4xl px-4 py-3 flex items-center justify-between border-b border-foreground/10 z-10">
        <div className="flex items-center gap-3">
          <Link
            to="/counsellor"
            className="p-1.5 text-foreground/60 hover:text-clay transition-colors rounded-full hover:bg-foreground/5"
            title="Return to Field Office"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-xl leading-none">CaseWriter Studio</h1>
              {selectedCase && (
                <span className="rounded-full bg-clay/15 px-2.5 py-0.5 font-mono text-[10px] font-bold text-clay border border-clay/25">
                  Target: {selectedCase.codeword}
                </span>
              )}
            </div>
            <p className="text-[11px] text-foreground/50 pt-0.5">
              Strict grounded inference using Bayesian risk evidence · PS-26094 production stack
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {cases.length > 0 && (
            <select
              value={selectedCase?.id || ""}
              onChange={(e) => {
                const found = cases.find((c) => c.id === e.target.value);
                if (found) setSelectedCase(found);
              }}
              className="text-xs rounded-full border border-foreground/15 bg-background px-3 py-1 text-foreground focus:outline-none focus:border-clay font-mono"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  Dossier: {c.codeword} ({c.triage_priority})
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={() => {
              setMessages([CASEWRITER_WELCOME]);
              if (typeof window !== "undefined") {
                localStorage.removeItem(`casewriter_chat_messages_${activeCodeword}`);
              }
            }}
            className="inline-flex items-center gap-1 rounded-full border border-foreground/15 bg-card/70 px-2.5 py-1 text-xs font-medium text-foreground/70 hover:border-clay hover:text-clay transition-colors cursor-pointer"
            title="Reset CaseWriter dialogue"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reset Chat</span>
          </button>

          <Link
            to="/counsellor"
            className="inline-flex items-center gap-1.5 rounded-full border border-foreground/15 bg-card/70 px-3 py-1 text-xs font-medium text-foreground hover:border-clay hover:text-clay transition-colors"
          >
            <Folder className="h-3.5 w-3.5 text-clay" />
            <span>Dossier Shelf</span>
          </Link>
        </div>
      </header>

      {/* CaseWriter Presets Ribbon */}
      <div className="mx-auto w-full max-w-4xl px-4 pt-3 pb-1 z-10">
        <div className="flex flex-wrap items-center gap-1.5 p-2 rounded-2xl bg-card/80 border border-foreground/10">
          <span className="text-[10px] font-mono uppercase tracking-wider text-foreground/50 mr-1">
            Clinical Presets:
          </span>
          {casewriterPresets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => handleSend(preset.prompt)}
              disabled={streaming}
              className="text-[11px] rounded-full border border-foreground/15 bg-background/70 px-3 py-1 text-foreground/75 hover:border-clay hover:text-clay transition-all disabled:opacity-40 text-left cursor-pointer"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto px-4 py-4 space-y-4 z-10">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${
              m.role === "user" ? "justify-end" : m.role === "system" ? "justify-center" : "justify-start"
            }`}
          >
            {m.role === "system" ? (
              <div className="max-w-lg rounded-2xl bg-card border border-foreground/15 p-3 text-center text-xs text-foreground/80 shadow-sm">
                {m.content}
              </div>
            ) : (
              <div
                className={`max-w-[88%] md:max-w-xl rounded-3xl p-4 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-clay text-white rounded-br-sm shadow-[var(--shadow-lift)]"
                    : "bg-card/95 text-foreground border border-clay/25 rounded-bl-sm shadow-[var(--shadow-soft)] backdrop-blur-sm"
                }`}
              >
                {/* Assistant Model Header Badge */}
                {m.role === "assistant" && (
                  <div className="flex items-center justify-between text-[10px] font-mono text-foreground/50 border-b border-foreground/5 pb-1.5 mb-2">
                    <span className="font-semibold uppercase tracking-wider flex items-center gap-1 text-clay">
                      <Scale className="h-3 w-3" />
                      <span>CaseWriter Evidence & Recommendation</span>
                    </span>
                    {m.source && (
                      <span className="text-[9px] bg-foreground/5 px-2 py-0.5 rounded font-mono">
                        {m.source === "vm_orchestrator"
                          ? "⚡ Live Azure VM"
                          : m.source === "backend_casewriter_engine"
                          ? "🛡️ Backend Synthesis"
                          : "🍃 Client Fallback"}
                      </span>
                    )}
                  </div>
                )}

                <div className="whitespace-pre-wrap font-sans text-xs md:text-sm leading-relaxed">
                  {m.content}
                </div>

                {m.role === "assistant" && streaming && i === messages.length - 1 && (
                  <span className="inline-block h-3 w-1.5 ml-1 bg-clay animate-pulse" />
                )}

                {/* Save to Case Dossier Button */}
                {m.role === "assistant" && m.content && !streaming && (
                  <div className="pt-3 mt-2 border-t border-foreground/10 flex items-center justify-between">
                    <span className="text-[10px] text-foreground/45 font-mono">
                      Grounded recommendation ready
                    </span>
                    <button
                      type="button"
                      onClick={() => handleSaveToDossier(m.content, i)}
                      disabled={savedNotes[i]}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-clay hover:underline disabled:opacity-50 cursor-pointer"
                    >
                      {savedNotes[i] ? (
                        <>
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          <span className="text-emerald-600">Saved to Case Notes</span>
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="h-3.5 w-3.5" />
                          <span>Save as Note to Dossier</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Message Input Box */}
      <div className="sticky bottom-0 z-20 w-full border-t border-foreground/10 bg-background/95 p-4 backdrop-blur-md">
        <div className="mx-auto max-w-4xl flex items-center gap-2">
          <input
            className="flex-1 rounded-full border border-foreground/15 bg-card px-5 py-3 text-sm text-foreground placeholder:text-foreground/40 focus:border-clay focus:outline-none focus:ring-1 focus:ring-clay"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Enter case facts, witness statements, or incident notes to synthesize recommendation..."
            maxLength={4000}
            disabled={streaming}
          />
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={streaming || !input.trim()}
            className="flex h-11 w-11 items-center justify-center rounded-full bg-clay text-white shadow-[var(--shadow-lift)] transition-all hover:bg-forest disabled:opacity-40 cursor-pointer active:scale-95"
            aria-label="Send to CaseWriter"
          >
            {streaming ? <Sparkles className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <div className="mx-auto max-w-4xl flex items-center justify-between text-[10px] text-foreground/40 pt-1.5 px-2 font-light">
          <span>CaseWriter v2.1.0 · Grounded Bayesian inference & policy compliance</span>
          <span className="font-mono">Port :8400 & :8500</span>
        </div>
      </div>
    </div>
  );
}
