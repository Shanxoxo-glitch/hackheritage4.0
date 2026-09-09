import { useState, useRef, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { streamChat } from "@/lib/api";
import {
  ArrowLeft,
  Send,
  Sparkles,
  PhoneCall,
  ShieldAlert,
  Wind,
  Compass,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export const Route = createFileRoute("/chat")({
  head: () => ({
    meta: [{ title: "Sanctuary Chat — Sahayak" }],
  }),
  component: CrisisChatPage,
});

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export default function CrisisChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to this quiet space. Take a soft breath. You don't have to explain everything, and you don't have to carry it all alone right now. What's resting on your mind?",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [showCrisisBanner, setShowCrisisBanner] = useState(false);
  const [showGroundingDrawer, setShowGroundingDrawer] = useState(false);
  const [groundingStep, setGroundingStep] = useState(0);

  const abortRef = useRef<(() => void) | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showCrisisBanner]);

  const groundingExercises = [
    {
      title: "5-4-3-2-1 Sensory Grounding",
      steps: [
        "👀 Notice 5 things you can see around you right now. Soft colors, shapes, shadows.",
        "✋ Feel 4 things you can touch. The fabric of your clothes, the coolness of the table.",
        "👂 Listen for 3 sounds. The distant hum of the fan, rustling leaves, your breath.",
        "👃 Identify 2 scents. Clean air, morning tea, or simply the room's scent.",
        "👅 Notice 1 taste. Take a gentle sip of cool water and feel it swallow.",
      ],
    },
  ];

  const handleSend = () => {
    if (!input.trim() || streaming) return;
    const userMsg = input;
    setInput("");

    // Danger keyword check for immediate reassurance & helpline escalation
    const lower = userMsg.toLowerCase();
    const isDanger =
      lower.includes("suicide") ||
      lower.includes("kill") ||
      lower.includes("die") ||
      lower.includes("end my life") ||
      lower.includes("no reason to live") ||
      lower.includes("hurt myself");

    if (isDanger) {
      setShowCrisisBanner(true);
    }

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "assistant", content: "" },
    ]);
    setStreaming(true);

    abortRef.current = streamChat(
      { case_id: "local_session", channel: "pwa", message: userMsg },
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
        if (final.status === "awaiting_counsellor") {
          setShowCrisisBanner(true);
          setMessages((prev) => [
            ...prev,
            {
              role: "system",
              content:
                "🤝 An alert has been prioritised for on-duty counsellor review. If you are in immediate physical danger, please tap the call button above or call 14416 right now.",
            },
          ]);
        }
      },
      (err) => {
        setStreaming(false);
        console.error(err);
      }
    );
  };

  return (
    <div className="grain min-h-screen bg-background text-foreground flex flex-col justify-between relative overflow-hidden">
      {/* Persistent Glowing Helpline Bar */}
      <div className="sticky top-0 z-30 w-full border-b border-forest/15 bg-forest/95 px-4 py-2.5 text-forest-foreground backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-breathe absolute inline-flex h-full w-full rounded-full bg-clay" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-clay" />
            </span>
            <span className="text-xs font-medium tracking-wide">
              Someone is here with you · India 24/7 Crisis Helplines
            </span>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="tel:14416"
              className="flex items-center gap-1.5 rounded-full bg-clay px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-clay-soft transition-colors"
            >
              <PhoneCall className="h-3 w-3" />
              <span>14416 (Tele-MANAS)</span>
            </a>
            <a
              href="tel:18005990019"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-forest-foreground/30 px-3 py-1 text-xs hover:bg-forest-deep transition-colors"
            >
              <span>1800-599-0019 (KIRAN)</span>
            </a>
          </div>
        </div>
      </div>

      {/* Subheader */}
      <header className="mx-auto w-full max-w-4xl px-4 py-3 flex items-center justify-between border-b border-foreground/10 z-10">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="p-1.5 text-foreground/60 hover:text-clay transition-colors rounded-full hover:bg-foreground/5"
            title="Return to Sanctuary"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="font-display text-xl leading-none">Sahayak Sanctuary</h1>
            <p className="text-[11px] text-foreground/50">Anonymous · Encrypted · Non-judgmental</p>
          </div>
        </div>

        <button
          onClick={() => setShowGroundingDrawer(!showGroundingDrawer)}
          className="flex items-center gap-1.5 rounded-full border border-foreground/15 bg-card/70 px-3 py-1 text-xs font-medium text-foreground hover:border-clay hover:text-clay transition-colors"
        >
          <Wind className="h-3.5 w-3.5 text-clay" />
          <span>Grounding Anchor</span>
          {showGroundingDrawer ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>
      </header>

      {/* Interactive Grounding Drawer */}
      {showGroundingDrawer && (
        <div className="mx-auto w-full max-w-4xl px-4 pt-2 z-20">
          <div className="rounded-2xl border border-clay/30 bg-card/95 p-4 shadow-[var(--shadow-lift)] backdrop-blur-md space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-clay flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5" /> {groundingExercises[0].title}
              </span>
              <span className="text-[11px] text-foreground/50">
                Step {groundingStep + 1} of {groundingExercises[0].steps.length}
              </span>
            </div>

            <p className="text-sm text-foreground/85 font-medium">
              {groundingExercises[0].steps[groundingStep]}
            </p>

            <div className="flex justify-between items-center pt-2">
              <button
                onClick={() => setGroundingStep(Math.max(0, groundingStep - 1))}
                disabled={groundingStep === 0}
                className="text-xs text-foreground/50 disabled:opacity-30 hover:text-clay"
              >
                Previous
              </button>
              <button
                onClick={() =>
                  setGroundingStep(
                    Math.min(groundingExercises[0].steps.length - 1, groundingStep + 1)
                  )
                }
                disabled={groundingStep === groundingExercises[0].steps.length - 1}
                className="rounded-full bg-forest px-4 py-1 text-xs font-medium text-forest-foreground hover:bg-clay transition-colors disabled:opacity-40"
              >
                Next Anchor
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SHOWPIECE: Living Breathing Orb */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center -z-0 opacity-40">
        <div className="animate-orb h-80 w-80 md:h-96 md:w-96 rounded-full bg-gradient-to-tr from-clay/20 via-sage/30 to-forest/15 blur-2xl" />
      </div>

      {/* Chat Messages Log */}
      <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto px-4 py-6 space-y-4 z-10">
        {/* Danger Alert Banner if triggered */}
        {showCrisisBanner && (
          <div className="rounded-2xl border-2 border-clay bg-clay/10 p-4 text-foreground shadow-[var(--shadow-lift)] space-y-2 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center gap-2 text-clay font-semibold text-sm">
              <ShieldAlert className="h-4 w-4" />
              <span>We hear the deep pain you are carrying right now.</span>
            </div>
            <p className="text-xs text-foreground/80 leading-relaxed">
              You do not have to walk through this alone. Trained people who care are on call this
              second across India. Please reach out directly:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <a
                href="tel:14416"
                className="rounded-full bg-clay px-4 py-1.5 text-xs font-medium text-white hover:bg-clay-soft transition-colors"
              >
                Call Tele-MANAS (14416)
              </a>
              <a
                href="tel:18005990019"
                className="rounded-full bg-forest px-4 py-1.5 text-xs font-medium text-forest-foreground hover:bg-forest-deep transition-colors"
              >
                Call KIRAN (1800-599-0019)
              </a>
              <Link
                to="/request"
                className="rounded-full border border-foreground/30 px-3 py-1.5 text-xs text-foreground hover:bg-card transition-colors"
              >
                Connect to Assigned Counsellor
              </Link>
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${
              m.role === "user"
                ? "justify-end"
                : m.role === "system"
                ? "justify-center"
                : "justify-start"
            }`}
          >
            {m.role === "system" ? (
              <div className="max-w-lg rounded-2xl bg-card border border-foreground/15 p-3 text-center text-xs text-foreground/80 shadow-sm">
                {m.content}
              </div>
            ) : (
              <div
                className={`max-w-[85%] md:max-w-xl rounded-3xl p-4 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-forest text-forest-foreground rounded-br-sm shadow-[var(--shadow-lift)]"
                    : "bg-card/90 text-foreground border border-foreground/10 rounded-bl-sm shadow-[var(--shadow-soft)] backdrop-blur-sm"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
                {m.role === "assistant" && streaming && i === messages.length - 1 && (
                  <span className="inline-block h-3 w-1.5 ml-1 bg-clay animate-pulse" />
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
            placeholder="Type anything here... take all the time you need"
            maxLength={4000}
            disabled={streaming}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            className="flex h-11 w-11 items-center justify-center rounded-full bg-forest text-forest-foreground shadow-[var(--shadow-lift)] transition-all hover:bg-clay disabled:opacity-40"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <div className="mx-auto max-w-4xl text-center text-[10px] text-foreground/40 pt-1.5 font-light">
          Encrypted & unrecorded · Press <kbd className="font-mono">Esc</kbd> anytime for Quick Exit
        </div>
      </div>
    </div>
  );
}
