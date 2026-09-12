import { useState, useEffect } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { generateCodeword, saveHelpRequest, setVictimSharePreference } from "@/lib/store";
import { ArrowLeft, ArrowRight, ShieldCheck, Check, Sparkles, Stamp, Copy, Shield, User, Mail, Phone } from "lucide-react";

export const Route = createFileRoute("/request")({
  head: () => ({
    meta: [{ title: "Confidential Help Request — Sahayak" }],
  }),
  component: HelpRequestPage,
});

const SUPPORT_TYPES = [
  {
    id: "emotional" as const,
    label: "Emotional Grounding",
    desc: "A calm ear for heavy grief, panic, loneliness, or emotional exhaustion.",
  },
  {
    id: "domestic" as const,
    label: "Confidential Safety Support",
    desc: "Strictly discreet guidance for difficult or unsafe domestic situations.",
  },
  {
    id: "crisis" as const,
    label: "Crisis Triage",
    desc: "Immediate human escalation for overwhelming distress or safety concerns.",
  },
  {
    id: "ongoing" as const,
    label: "Ongoing Counselling",
    desc: "Setting up a regular, anonymous check-in rhythm with an assigned listener.",
  },
];

const CONSENT_SCOPES = [
  { key: "chatAnalysis", label: "Analyze my messages for wellbeing and distress indicators", required: true },
  { key: "escalationLadder", label: "Escalation ladder if I miss check-ins or express acute distress", required: true },
  { key: "voiceSignals", label: "Voice stress telemetry (optional audio check-in)", required: false },
  { key: "emailCheckin", label: "Quiet reminder check-ins (optional)", required: false },
  { key: "smsCheckin", label: "Discreet SMS notifications (optional)", required: false },
];

export default function HelpRequestPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [codeword, setCodeword] = useState("");
  const [supportType, setSupportType] = useState<"emotional" | "domestic" | "crisis" | "ongoing">("emotional");
  const [contactMethod, setContactMethod] = useState<"in_app" | "callback" | "quiet_checkin">("in_app");
  const [callbackWindow, setCallbackWindow] = useState("Evening 7:00 PM - 8:30 PM");
  const [notes, setNotes] = useState("");
  const [consent, setConsent] = useState<Record<string, boolean>>({
    chatAnalysis: true,
    escalationLadder: true,
    voiceSignals: false,
    emailCheckin: false,
    smsCheckin: false,
  });
  const [copied, setCopied] = useState(false);
  const [sharePersonalInfo, setSharePersonalInfo] = useState(false);
  const [victimName, setVictimName] = useState("");
  const [victimContact, setVictimContact] = useState("");

  useEffect(() => {
    setCodeword(generateCodeword());
  }, []);

  const toggleConsent = (key: string) => {
    setConsent((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCopyCodeword = () => {
    navigator.clipboard.writeText(codeword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSubmit = () => {
    const selectedSupport = SUPPORT_TYPES.find((s) => s.id === supportType);
    setVictimSharePreference({
      share: sharePersonalInfo,
      name: sharePersonalInfo ? victimName : undefined,
      email: sharePersonalInfo ? victimContact : undefined,
      phone: sharePersonalInfo ? victimContact : undefined,
    });

    saveHelpRequest({
      codeword,
      supportType,
      supportTypeLabel: selectedSupport?.label || "Support",
      contactMethod,
      callbackWindow: contactMethod === "callback" ? callbackWindow : undefined,
      notes: notes.trim() || undefined,
      consentScopes: {
        chatAnalysis: !!consent.chatAnalysis,
        voiceSignals: !!consent.voiceSignals,
        emailCheckin: !!consent.emailCheckin,
        smsCheckin: !!consent.smsCheckin,
        escalationLadder: !!consent.escalationLadder,
      },
      status: "new",
    });
    setStep(4); // Move to wax seal confirmation
  };

  return (
    <div className="grain min-h-screen bg-background text-foreground flex flex-col justify-between p-6 md:p-12 relative overflow-hidden">
      {/* Top Header */}
      <div className="mx-auto w-full max-w-xl flex items-center justify-between z-10">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Sanctuary</span>
        </Link>
        <span className="font-display text-lg text-foreground/70">Confidential Intake</span>
        <span className="text-xs text-foreground/40 font-mono tracking-widest">
          {step <= 3 ? `0${step} / 03` : "Sealed"}
        </span>
      </div>

      {/* Main Parchment Card */}
      <div className="mx-auto w-full max-w-xl my-auto py-8 z-10">
        {/* Step 1: Support Type */}
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-6 shadow-[var(--shadow-soft)]">
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                Step 01 · Support Form
              </span>
              <h2 className="text-3xl md:text-4xl font-display">What kind of care do you need?</h2>
              <p className="text-xs text-foreground/60 leading-relaxed">
                Everything here is pseudonymous. No government ID, no full name, and no phone
                numbers required unless you explicitly request a phone callback.
              </p>
            </div>

            <div className="space-y-2.5 pt-2">
              {SUPPORT_TYPES.map((st) => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => setSupportType(st.id)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all ${
                    supportType === st.id
                      ? "border-clay bg-card shadow-[var(--shadow-lift)] ring-1 ring-clay"
                      : "border-foreground/10 bg-card/40 hover:bg-card/80"
                  }`}
                >
                  <div className="font-display text-lg text-foreground">{st.label}</div>
                  <div className="text-xs text-foreground/60 mt-1">{st.desc}</div>
                </button>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="inline-flex items-center gap-2 rounded-full bg-forest px-7 py-3 text-sm font-medium text-forest-foreground hover:bg-clay transition-colors"
              >
                <span>Choose Delivery</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Contact Preference & Note */}
        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-6 shadow-[var(--shadow-soft)]">
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                Step 02 · Delivery Sanctuary
              </span>
              <h2 className="text-3xl md:text-4xl font-display">How should we connect?</h2>
              <p className="text-xs text-foreground/60">
                You dictate the boundary. No unsolicited contact will ever occur.
              </p>
            </div>

            <div className="space-y-3">
              {[
                {
                  id: "in_app" as const,
                  title: "In-App Quiet Chat Only",
                  desc: "All messages remain inside your browser on this device. Zero outside contact.",
                },
                {
                  id: "callback" as const,
                  title: "Discreet Callback Window",
                  desc: "A counsellor calls you strictly during your designated safe time window.",
                },
                {
                  id: "quiet_checkin" as const,
                  title: "Passive Daily Check-in Ladder",
                  desc: "A steady prompt appears in your app once daily. If missed, gentle escalation triggers.",
                },
              ].map((method) => (
                <button
                  key={method.id}
                  type="button"
                  onClick={() => setContactMethod(method.id)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all ${
                    contactMethod === method.id
                      ? "border-clay bg-card shadow-[var(--shadow-lift)] ring-1 ring-clay"
                      : "border-foreground/10 bg-card/40 hover:bg-card/80"
                  }`}
                >
                  <div className="text-sm font-medium text-foreground">{method.title}</div>
                  <div className="text-xs text-foreground/60 mt-0.5">{method.desc}</div>
                </button>
              ))}

              {contactMethod === "callback" && (
                <div className="pt-2 animate-in fade-in duration-300">
                  <label className="text-xs text-foreground/70 block mb-1 font-medium">
                    Designated Safe Window
                  </label>
                  <input
                    type="text"
                    value={callbackWindow}
                    onChange={(e) => setCallbackWindow(e.target.value)}
                    placeholder="e.g. Evenings between 7 PM - 8 PM"
                    className="w-full rounded-xl border border-foreground/15 bg-background p-3 text-sm focus:border-clay focus:outline-none"
                  />
                </div>
              )}

              <div>
                <label className="text-xs text-foreground/70 block mb-1 font-medium">
                  Confidential Context Note (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  placeholder="Share anything you want the counsellor to know beforehand..."
                  className="w-full rounded-xl border border-foreground/15 bg-background p-3 text-sm focus:border-clay focus:outline-none"
                />
              </div>

              {/* Circular Switch Toggle: Personal Info Sharing Choice */}
              <div className="rounded-2xl border border-foreground/15 bg-card p-5 space-y-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-0.5">
                    <span className="text-sm font-semibold text-foreground block">
                      Share Personal Info with Counsellor
                    </span>
                    <span className="text-xs text-foreground/60 block leading-relaxed">
                      {sharePersonalInfo
                        ? "Counsellor receives your direct contact info for coordinated clinical support."
                        : "Strict pseudonymity active. The counsellor only interacts using your secret codeword."}
                    </span>
                  </div>

                  {/* Circular switch toggle */}
                  <button
                    type="button"
                    role="switch"
                    aria-checked={sharePersonalInfo}
                    onClick={() => setSharePersonalInfo(!sharePersonalInfo)}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      sharePersonalInfo ? "bg-forest" : "bg-foreground/20"
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                        sharePersonalInfo ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {sharePersonalInfo && (
                  <div className="space-y-3 pt-3 border-t border-foreground/10 animate-in fade-in duration-300">
                    <div className="grid sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-foreground/70 block mb-1 font-medium">
                          Your Name / Preferred Name
                        </label>
                        <input
                          type="text"
                          value={victimName}
                          onChange={(e) => setVictimName(e.target.value)}
                          placeholder="e.g. Maya or Full Name"
                          className="w-full rounded-xl border border-foreground/15 bg-background p-2.5 text-xs focus:border-clay focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-foreground/70 block mb-1 font-medium">
                          Direct Contact (Phone or Email)
                        </label>
                        <input
                          type="text"
                          value={victimContact}
                          onChange={(e) => setVictimContact(e.target.value)}
                          placeholder="+91 98765 43210 or email"
                          className="w-full rounded-xl border border-foreground/15 bg-background p-2.5 text-xs focus:border-clay focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                )}

                <div className="text-[11px] text-foreground/45 italic font-mono pt-1">
                  {sharePersonalInfo
                    ? "Status: Identity Disclosed (Confidential Care)"
                    : "Status: 100% Shielded (Codeword Only)"}
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-between items-center">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-foreground/60 hover:text-clay"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="inline-flex items-center gap-2 rounded-full bg-forest px-7 py-3 text-sm font-medium text-forest-foreground hover:bg-clay transition-colors"
              >
                <span>Review Consent</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Plain-Language Consent Toggles */}
        {step === 3 && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-6 shadow-[var(--shadow-soft)]">
            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                Step 03 · Informed Agency
              </span>
              <h2 className="text-3xl md:text-4xl font-display">Your explicit choices</h2>
              <p className="text-xs text-foreground/60">
                You retain complete control. You can revoke any scope anytime.
              </p>
            </div>

            <div className="divide-y divide-foreground/10 border-y border-foreground/10 py-1">
              {CONSENT_SCOPES.map((scope) => (
                <label
                  key={scope.key}
                  className="flex items-start gap-3.5 py-3.5 cursor-pointer hover:bg-foreground/5 px-2 rounded-xl transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={!!consent[scope.key]}
                    onChange={() => !scope.required && toggleConsent(scope.key)}
                    disabled={scope.required}
                    className="mt-0.5 h-4 w-4 rounded border-foreground/30 accent-clay"
                  />
                  <div className="flex-1 text-xs leading-relaxed text-foreground/85">
                    <span>{scope.label}</span>
                    {scope.required && (
                      <span className="ml-2 text-[10px] text-clay font-medium uppercase tracking-wider">
                        Required for triage
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>

            <div className="pt-2 flex justify-between items-center">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="text-xs text-foreground/60 hover:text-clay"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                className="inline-flex items-center gap-2 rounded-full bg-clay px-8 py-3.5 text-sm font-medium text-white shadow-[var(--shadow-lift)] hover:bg-forest transition-all"
              >
                <span>Seal with Codeword</span>
                <Sparkles className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: SHOWPIECE Wax-Seal Confirmation */}
        {step === 4 && (
          <div className="animate-in zoom-in-95 duration-700 rounded-3xl border border-clay/30 bg-card p-8 md:p-10 text-center space-y-8 shadow-[var(--shadow-soft)] relative overflow-hidden">
            {/* Wax seal stamp */}
            <div className="relative mx-auto flex items-center justify-center">
              <div className="animate-stamp flex h-24 w-24 items-center justify-center rounded-full bg-clay text-white shadow-2xl border-4 border-clay-soft/40">
                <Stamp className="h-10 w-10 text-white/95" />
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-[10px] font-medium uppercase tracking-[0.25em] text-clay">
                Request Sealed & Confidential
              </span>
              <h2 className="text-4xl font-display text-foreground">Your secret codeword</h2>
              <p className="text-xs text-foreground/65 max-w-sm mx-auto">
                Keep this code written down or memorized. It is the only key to review your status
                or speak with your assigned counsellor.
              </p>
            </div>

            {/* Codeword Box */}
            <div className="mx-auto max-w-sm rounded-2xl border-2 border-dashed border-clay/50 bg-background/80 p-4 flex items-center justify-between">
              <span className="font-mono text-xl font-bold tracking-wider text-clay">
                {codeword}
              </span>
              <button
                type="button"
                onClick={handleCopyCodeword}
                className="flex items-center gap-1.5 rounded-lg bg-foreground/5 px-3 py-1.5 text-xs text-foreground/80 hover:bg-clay hover:text-white transition-colors"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row justify-center gap-3">
              <Link
                to="/status"
                className="rounded-full bg-forest px-8 py-3 text-sm font-medium text-forest-foreground hover:bg-clay transition-colors"
              >
                View Case Status
              </Link>
              <Link
                to="/chat"
                className="rounded-full border border-foreground/20 px-6 py-3 text-sm font-medium text-foreground hover:border-clay hover:text-clay transition-colors"
              >
                Continue in Chat
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Footer */}
      <div className="mx-auto w-full max-w-xl text-center text-xs text-foreground/40 font-light z-10">
        No personal identification is ever stored · End-to-end pseudonymous
      </div>
    </div>
  );
}
