// shared/api.ts — the API client matching the PS26094 stack guide
const BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "";

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
  body: { case_id: string; channel: string; message: string; language?: string },
  onDelta: (text: string) => void,
  onFinal: (data: { thread_id: string; status: string; audit_ref: string; reply: string }) => void,
  onError: (err: string) => void
): () => void {
  const controller = new AbortController();

  if (!BASE) {
    // Standalone / Offline interactive demo streamer
    let isAborted = false;
    controller.signal.addEventListener("abort", () => {
      isAborted = true;
    });

    const msgLower = body.message.toLowerCase();
    const isCrisis =
      msgLower.includes("die") ||
      msgLower.includes("kill") ||
      msgLower.includes("end it") ||
      msgLower.includes("suicide") ||
      msgLower.includes("hurt myself") ||
      msgLower.includes("no reason to live");

    const category = isCrisis
      ? "crisis"
      : msgLower.includes("ground") || msgLower.includes("breathe") || msgLower.includes("panic")
      ? "grounding"
      : msgLower.includes("alone") || msgLower.includes("lonely")
      ? "lonely"
      : "default";

    const responseTemplates = SCRIPTED_RESPONSES[category];
    const fullReply = responseTemplates.join(" ");

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
        });
      }
    }, 45);

    return () => {
      isAborted = true;
      clearInterval(interval);
    };
  }

  // Live SSE connection to backend
  fetch(`${BASE}/v1/interactions/stream`, {
    method: "POST",
    headers: { ...headers("victim"), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "include",
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.body) {
        onError("no body");
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n\n");
        buf = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.delta) onDelta(data.delta);
            if (data.final) onFinal(data.final);
            if (data.error) onError(data.error);
          } catch (e) {
            console.error("Failed to parse SSE payload", e);
          }
        }
      }
    })
    .catch((e) => {
      if (e.name !== "AbortError") onError(e.message);
    });

  return () => controller.abort();
}
