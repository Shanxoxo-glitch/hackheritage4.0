import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getHelpRequests, getActiveCodeword, HelpRequest } from "@/lib/store";
import { ArrowLeft, Search, ShieldCheck, HeartHandshake, Clock, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/status")({
  head: () => ({
    meta: [{ title: "Confidential Case Status — Sahayak" }],
  }),
  component: CaseStatusPage,
});

export default function CaseStatusPage() {
  const [activeCode, setActiveCode] = useState("");
  const [requests, setRequests] = useState<HelpRequest[]>([]);
  const [matchedRequest, setMatchedRequest] = useState<HelpRequest | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const list = getHelpRequests();
    setRequests(list);
    const storedCode = getActiveCodeword();
    if (storedCode) {
      setActiveCode(storedCode);
      const found = list.find((r) => r.codeword.toLowerCase() === storedCode.toLowerCase());
      if (found) setMatchedRequest(found);
    } else if (list.length > 0) {
      setActiveCode(list[0].codeword);
      setMatchedRequest(list[0]);
    }
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearched(true);
    const found = requests.find((r) => r.codeword.toLowerCase() === activeCode.trim().toLowerCase());
    setMatchedRequest(found || null);
  };

  const getStepProgress = (status: HelpRequest["status"]) => {
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

  const progress = matchedRequest ? getStepProgress(matchedRequest.status) : 1;

  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-2xl space-y-8">
        {/* Header */}
        <div className="space-y-2 border-b border-foreground/10 pb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Sanctuary</span>
          </Link>
          <h1 className="text-4xl md:text-5xl font-display">Check-in Status</h1>
          <p className="text-sm text-foreground/65">
            Enter your secret codeword to check if your counsellor has responded.
          </p>
        </div>

        {/* Codeword Search Form */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={activeCode}
              onChange={(e) => setActiveCode(e.target.value)}
              placeholder="Enter your codeword (e.g. quiet-river-17)"
              className="w-full rounded-full border border-foreground/20 bg-card px-5 py-3 text-sm font-mono text-foreground focus:border-clay focus:outline-none focus:ring-1 focus:ring-clay"
            />
          </div>
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-3 text-sm font-medium text-forest-foreground hover:bg-clay transition-colors"
          >
            <Search className="h-4 w-4" />
            <span>Look up</span>
          </button>
        </form>

        {/* Case Details Card */}
        {matchedRequest ? (
          <div className="rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-8 shadow-[var(--shadow-soft)] animate-in fade-in duration-500">
            {/* Codeword ribbon */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-foreground/10 pb-4">
              <div>
                <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                  Active Sanctuary Case
                </span>
                <h2 className="font-mono text-2xl font-bold text-foreground">
                  {matchedRequest.codeword}
                </h2>
              </div>
              <span className="self-start rounded-full bg-forest/10 px-3.5 py-1 text-xs font-medium text-forest">
                {matchedRequest.supportTypeLabel}
              </span>
            </div>

            {/* Timeline Progress Ribbon */}
            <div className="space-y-4">
              <span className="text-xs text-foreground/50 uppercase tracking-wider block">
                Care Journey Milestone
              </span>
              <div className="relative flex justify-between items-center text-center">
                <div className="absolute top-1/2 left-4 right-4 -translate-y-1/2 h-0.5 bg-foreground/15 -z-0" />
                <div
                  className="absolute top-1/2 left-4 -translate-y-1/2 h-0.5 bg-clay transition-all duration-500 -z-0"
                  style={{ width: `${((progress - 1) / 3) * 100}%` }}
                />

                {[
                  { n: 1, label: "Received", desc: "Sealed securely" },
                  { n: 2, label: "Assigned", desc: "Matched to listener" },
                  { n: 3, label: "In Support", desc: "Holding space" },
                  { n: 4, label: "Stabilized", desc: "Closed with care" },
                ].map((item) => {
                  const isDone = progress >= item.n;
                  const isCurrent = progress === item.n;
                  return (
                    <div key={item.n} className="flex flex-col items-center z-10">
                      <div
                        className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                          isDone
                            ? "bg-clay text-white shadow-md ring-2 ring-clay/30"
                            : "bg-card border border-foreground/20 text-foreground/40"
                        }`}
                      >
                        {isDone ? <CheckCircle2 className="h-4 w-4" /> : item.n}
                      </div>
                      <span
                        className={`mt-2 text-xs font-medium ${
                          isCurrent ? "text-clay font-bold" : "text-foreground/75"
                        }`}
                      >
                        {item.label}
                      </span>
                      <span className="text-[10px] text-foreground/45 hidden sm:block">
                        {item.desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Reassuring Details */}
            <div className="grid sm:grid-cols-2 gap-4 pt-2">
              <div className="rounded-2xl bg-background/60 p-4 border border-foreground/5">
                <span className="text-xs text-foreground/50 block mb-1">Assigned Counsellor</span>
                <span className="font-display text-xl text-foreground flex items-center gap-2">
                  <HeartHandshake className="h-4 w-4 text-clay" />
                  {matchedRequest.assignedCounsellor || "Dr. Ananya Roy (On Duty)"}
                </span>
              </div>
              <div className="rounded-2xl bg-background/60 p-4 border border-foreground/5">
                <span className="text-xs text-foreground/50 block mb-1">Contact Protocol</span>
                <span className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4 text-sage-deep" />
                  {matchedRequest.contactMethod === "callback"
                    ? matchedRequest.callbackWindow || "Evening Window"
                    : "In-App Quiet Chat"}
                </span>
              </div>
            </div>

            {/* Direct Action */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link
                to="/chat"
                className="flex-1 rounded-full bg-forest py-3 text-center text-sm font-medium text-forest-foreground hover:bg-clay transition-colors"
              >
                Open Sanctuary Chat
              </Link>
              <Link
                to="/help"
                className="rounded-full border border-foreground/20 px-6 py-3 text-center text-sm font-medium text-foreground hover:bg-card transition-colors"
              >
                Emergency Helplines
              </Link>
            </div>
          </div>
        ) : searched ? (
          <div className="rounded-3xl border border-dashed border-foreground/20 p-8 text-center space-y-3">
            <p className="font-display text-2xl text-foreground/70">No request found for this code</p>
            <p className="text-xs text-foreground/50">
              Please double check the spelling of your codeword or file a new confidential intake.
            </p>
            <Link
              to="/request"
              className="inline-block rounded-full bg-clay px-6 py-2.5 text-xs font-medium text-white hover:bg-forest transition-colors"
            >
              Start confidential intake
            </Link>
          </div>
        ) : null}

        {/* Quick hint */}
        <div className="text-center text-xs text-foreground/45 flex items-center justify-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-sage-deep" />
          <span>Only your own case details are visible. No scores or telemetry are exposed.</span>
        </div>
      </div>
    </div>
  );
}
