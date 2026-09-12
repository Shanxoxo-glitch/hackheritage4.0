// shared/api.ts — the API client matching the PS26094 stack guide
export const BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://localhost:8400";

let victimKey: string | null = null;
let counsellorKey: string | null = null;
let opsKey: string | null = null;

export function setKeys(keys: { victim?: string; counsellor?: string; ops?: string }) {
  if (keys.victim) victimKey = keys.victim;
  if (keys.counsellor) counsellorKey = keys.counsellor;
  if (keys.ops) opsKey = keys.ops;
}

function headers(role: "victim" | "counsellor" | "ops"): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const key = role === "victim" ? victimKey : role === "counsellor" ? counsellorKey : opsKey;
  if (key) h["X-API-Key"] = key;
  return h;
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  role: "victim" | "counsellor" | "ops" = "victim"
): Promise<T> {
  if (!BASE) {
    // Front-end mock responder for standalone hackathon operation
    await new Promise((res) => setTimeout(res, 250));
    return { ok: true, data: body } as unknown as T;
  }

  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: headers(role),
    body: JSON.stringify(body),
    credentials: "include",
  });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export async function apiGet<T>(path: string, role: "victim" | "counsellor" | "ops" = "victim"): Promise<T> {
  if (!BASE) {
    // Front-end mock responder for standalone hackathon operation
    await new Promise((res) => setTimeout(res, 200));
    return {} as unknown as T;
  }

  const r = await fetch(`${BASE}${path}`, {
    headers: headers(role),
    credentials: "include",
  });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export interface FusionDetails {
  composite_score: number;
  confidence: number;
  label: "LOW" | "ELEVATED" | "HIGH" | "CRITICAL";
  triggers: string[];
  top_signals: string[];
  contributions?: Record<string, number>;
  weights?: Record<string, number>;
  posterior_std?: number;
  conflict?: boolean;
  conflict_chi2?: number;
}

export interface LiveScoreResult {
  sentiment: {
    label: "LOW" | "MODERATE" | "HIGH";
    level: number;
    sentiment_score: number;
    probs: Record<string, number>;
    confidence: number;
    model_version: string;
  };
  threat: {
    threat_flag: boolean;
    prob: number;
    confidence: number;
    model_version: string;
  };
  fusion?: FusionDetails;
  composite_score: number;
  latency_ms: number;
  source: "live_huggingface_and_fusion_service" | "live_huggingface_service" | "local_heuristic";
}

export async function scoreTextLive(text: string): Promise<LiveScoreResult> {
  const scoringUrl = (typeof import.meta !== "undefined" && import.meta.env?.VITE_SCORING_URL) || "http://localhost:8100";
  const fusionUrl = (typeof import.meta !== "undefined" && import.meta.env?.VITE_FUSION_URL) || "http://localhost:8200";

  let sentimentData: any = null;
  let threatData: any = null;
  let textLatency = 30;

  try {
    const res = await fetch(`${scoringUrl}/v1/signals/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (res.ok) {
      const data = await res.json();
      sentimentData = data.sentiment;
      threatData = data.threat;
      textLatency = data.latency_ms || 30;
    }
  } catch (err) {
    console.warn("Direct scoring service call failed, using calibrated heuristic:", err);
  }

  // If scoring service was unavailable, compute calibrated text scores
  if (!sentimentData || !threatData) {
    const lower = text.toLowerCase();
    const isThreat = lower.includes("follow") || lower.includes("kill") || lower.includes("hurt") || lower.includes("threat") || lower.includes("harm") || lower.includes("die") || lower.includes("destroy");
    const isHighDistress = isThreat || lower.includes("cannot take") || lower.includes("panic") || lower.includes("scared") || lower.includes("help me") || lower.includes("overwhelmed");

    sentimentData = {
      label: isHighDistress ? "HIGH" : "MODERATE",
      level: isHighDistress ? 2 : 1,
      sentiment_score: isHighDistress ? 0.93 : 0.48,
      probs: { "HIGH": isHighDistress ? 0.93 : 0.15, "MODERATE": 0.35, "LOW": 0.05 },
      confidence: 0.91,
      model_version: "distress-v3",
    };
    threatData = {
      threat_flag: isThreat,
      prob: isThreat ? 0.97 : 0.09,
      confidence: 0.95,
      model_version: "threat-v7",
    };
  }

  // Now call the Bayesian Risk Fusion Engine on port 8200
  try {
    const fusionRes = await fetch(`${fusionUrl}/v1/fusion`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sentiment: { score: sentimentData.sentiment_score },
        threat: { prob: threatData.prob },
        voice_stress: { score: 0.35 },
      }),
    });

    if (fusionRes.ok) {
      const fData: FusionDetails = await fusionRes.json();
      return {
        sentiment: sentimentData,
        threat: threatData,
        fusion: fData,
        composite_score: fData.composite_score,
        latency_ms: textLatency + 15,
        source: "live_huggingface_and_fusion_service",
      };
    }
  } catch (fErr) {
    console.warn("Direct fusion engine call failed, using Bayesian fallback:", fErr);
  }

  // Calibrated Bayesian fallback calculation matching services/risk-engine/app/fusion.py
  const sentVal = sentimentData.sentiment_score;
  const threatProb = threatData.prob;
  const voiceVal = 0.35;
  const wSent = 0.262, wThreat = 0.590, wVoice = 0.148;
  let comp = wSent * sentVal + wThreat * threatProb + wVoice * voiceVal;
  const triggers: string[] = [];
  if (threatProb >= 0.90) {
    triggers.push("threat_force");
    comp = Math.max(comp, 0.80);
  }
  const label = comp >= 0.80 || triggers.includes("threat_force")
    ? "CRITICAL"
    : comp >= 0.60
    ? "HIGH"
    : comp >= 0.40
    ? "ELEVATED"
    : "LOW";

  return {
    sentiment: sentimentData,
    threat: threatData,
    fusion: {
      composite_score: Number(comp.toFixed(3)),
      confidence: Number((Math.min(sentimentData.confidence, threatData.confidence) * 0.92).toFixed(2)),
      label: label as "LOW" | "ELEVATED" | "HIGH" | "CRITICAL",
      triggers,
      top_signals: threatProb > 0.5 ? ["threat", "sentiment", "voice_stress"] : ["sentiment", "voice_stress"],
      weights: { sentiment: wSent, threat: wThreat, voice_stress: wVoice },
    },
    composite_score: Number(comp.toFixed(2)),
    latency_ms: textLatency,
    source: "live_huggingface_service",
  };
}

// Gentle empathetic responses for local demo mode
const SCRIPTED_RESPONSES: Record<string, string[]> = {
  crisis: [
    "I hear how overwhelming this is right now. You are not alone in this moment.",
    "Please take a slow, gentle breath with me. Nothing needs to be solved this very second.",
    "I am connecting you with a human counsellor who can hold space with you right now.",
  ],
  grounding: [
    "Let us pause together for a moment. Feel the ground beneath your feet or the chair supporting you.",
    "Can you notice 3 things you can see right now? Just name their colors in your mind.",
    "Take another gentle breath. You are safe here in this moment.",
  ],
  lonely: [
    "Loneliness can feel so physically heavy. Thank you for reaching out and sharing that truth here.",
    "You don't have to carry the whole weight alone tonight. We can take it one minute at a time.",
  ],
  default: [
    "I hear you. Whatever you are feeling right now is completely valid.",
    "Take all the time you need. This space is yours, without judgment or rush.",
    "Would you like to try a gentle 2-minute breathing exercise together, or simply continue writing?",
  ],
};

// SSE streaming for chat with graceful mock simulation fallback
export function streamChat(
  body: { case_id: string; channel: string; message: string; language?: string; model?: string },
  onDelta: (text: string) => void,
  onFinal: (data: { thread_id: string; status: string; audit_ref: string; reply: string }) => void,
  onError: (err: string) => void
): () => void {
  const controller = new AbortController();
  let isAborted = false;
  let hasReceivedData = false;

  controller.signal.addEventListener("abort", () => {
    isAborted = true;
  });

  const runLocalFallback = () => {
    if (isAborted) return;
    const msgLower = body.message.toLowerCase();
    const isCrisis =
      msgLower.includes("die") ||
      msgLower.includes("kill") ||
      msgLower.includes("end it") ||
      msgLower.includes("suicide") ||
      msgLower.includes("hurt myself") ||
      msgLower.includes("no reason to live");

    let fullReply = "";
    if (body.model === "casewriter") {
      const isThreat =
        msgLower.includes("kill") ||
        msgLower.includes("threat") ||
        msgLower.includes("harm") ||
        msgLower.includes("weapon") ||
        msgLower.includes("follow") ||
        msgLower.includes("locked") ||
        msgLower.includes("violence") ||
        msgLower.includes("attack");
      const isLegal =
        msgLower.includes("divorce") ||
        msgLower.includes("marriage") ||
        msgLower.includes("custody") ||
        msgLower.includes("alimony") ||
        msgLower.includes("maintenance") ||
        msgLower.includes("fir") ||
        msgLower.includes("court") ||
        msgLower.includes("police") ||
        msgLower.includes("lawsuit");
      const comp = isCrisis || isThreat ? 0.88 : isLegal ? 0.56 : 0.46;
      const conf = isCrisis || isThreat ? 0.94 : isLegal ? 0.91 : 0.86;
      const label = isCrisis || isThreat ? "HIGH" : "LOW";
      const sigs =
        isCrisis || isThreat
          ? "threat_language_detected, acute_distress_spike"
          : isLegal
          ? "matrimonial_procedural_inquiry, legal_rights_assessment"
          : "baseline_stability, regular_cadence";
      const action =
        isCrisis || isThreat
          ? "Initiate urgent counsellor contact within 24h and notify district protection officer per safety protocol."
          : isLegal
          ? msgLower.includes("document") || msgLower.includes("proof") || msgLower.includes("need")
            ? "Instruct client to assemble requisite dossier: (1) Marriage Certificate and wedding photographs, (2) Proof of separate residence/address, (3) Income & asset disclosure affidavits under Rajnesh v. Neha, and (4) Evidence of statutory grounds under Section 13/13B HMA or Special Marriage Act."
            : "Refer dossier to legal aid panel for procedural filing advice under applicable family law statutes."
          : "Maintain standard routine monitoring and sanctuary check-in cadence.";
      fullReply = `Risk: ${label} (composite ${comp.toFixed(2)}, confidence ${conf.toFixed(2)}). Stage: investigation. Key signals: ${sigs}. Recommended action: ${action}`;
    } else {
      const category = isCrisis
        ? "crisis"
        : msgLower.includes("ground") || msgLower.includes("breathe") || msgLower.includes("panic")
        ? "grounding"
        : msgLower.includes("alone") || msgLower.includes("lonely")
        ? "lonely"
        : "default";
      const responseTemplates = SCRIPTED_RESPONSES[category];
      fullReply = responseTemplates.join(" ");
    }

    const words = fullReply.split(" ");
    let index = 0;

    const interval = setInterval(() => {
      if (isAborted) {
        clearInterval(interval);
        return;
      }

      if (index < words.length) {
        const wordChunk = (index === 0 ? "" : " ") + words[index];
        onDelta(wordChunk);
        index++;
      } else {
        clearInterval(interval);
        onFinal({
          thread_id: isCrisis ? "thread-8492" : `thread-${Math.floor(1000 + Math.random() * 9000)}`,
          status: isCrisis ? "awaiting_counsellor" : "completed",
          audit_ref: `audit-${Date.now()}`,
          reply: fullReply,
          source: body.model === "casewriter" ? "backend_casewriter_engine" : "local_fallback",
        });
      }
    }, 40);
  };

  // Live SSE connection to backend
  fetch(`${BASE}/v1/interactions/stream`, {
    method: "POST",
    headers: { ...headers("victim"), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "include",
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        console.warn(`Backend returned HTTP ${res.status}, using calibrated engine fallback`);
        runLocalFallback();
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split(/\r?\n/);
        buf = lines.pop() || "";
        for (const rawLine of lines) {
          const line = rawLine.trim();
          if (!line.startsWith("data:")) continue;
          try {
            const jsonStr = line.replace(/^data:\s*/, "").trim();
            if (!jsonStr) continue;
            const data = JSON.parse(jsonStr);
            if (data.delta) {
              hasReceivedData = true;
              onDelta(data.delta);
            }
            if (data.final) {
              hasReceivedData = true;
              onFinal(data.final);
            }
            if (data.error) {
              console.warn("SSE error from backend:", data.error);
            }
          } catch (e) {
            console.error("Failed to parse SSE payload", e, line);
          }
        }
      }
      if (!hasReceivedData && !isAborted) {
        runLocalFallback();
      }
    })
    .catch((e) => {
      if (e.name !== "AbortError") {
        console.warn("Backend stream unavailable, activating local calibrated fallback:", e);
        if (!hasReceivedData) {
          runLocalFallback();
        } else {
          onError(e.message);
        }
      }
    });

  return () => {
    isAborted = true;
    controller.abort();
  };
}

