export interface CheckInEntry {
  id: string;
  date: string; // YYYY-MM-DD
  mood: 1 | 2 | 3 | 4 | 5;
  moodLabel: string;
  sleepHours: number;
  sleepQuality: string;
  feelings: string[];
  reflection?: string;
  createdAt: number;
}

export interface HelpRequest {
  id: string;
  codeword: string;
  supportType: "emotional" | "domestic" | "crisis" | "ongoing";
  supportTypeLabel: string;
  contactMethod: "in_app" | "callback" | "quiet_checkin";
  callbackWindow?: string;
  notes?: string;
  consentScopes: {
    chatAnalysis: boolean;
    voiceSignals: boolean;
    emailCheckin: boolean;
    smsCheckin: boolean;
    escalationLadder: boolean;
  };
  status: "new" | "contacted" | "in_support" | "resolved";
  createdAt: string;
  assignedCounsellor?: string;
}

export interface VictimHistoryItem {
  id: string;
  timestamp: string;
  text: string;
  source: "chat" | "questionnaire" | "intake";
  risk_level?: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  details?: string;
}

export interface TriageAlert {
  alert_id: string;
  case_id: string;
  thread_id: string;
  risk_level: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  composite_score: number;
  confidence: number;
  triage_priority_score: number;
  raised_at: string;
  decision_status: "pending" | "approved" | "rejected";
  counsellor_note?: string;
  reasons: string[];
  channel: string;
  victim_text?: string;
  victim_info?: {
    codeword: string;
    share_personal_info: boolean;
    name?: string;
    email?: string;
    latest_mood?: string;
    latest_sleep?: string;
    history_count: number;
  };
  history?: VictimHistoryItem[];
}

export interface CaseNote {
  id: string;
  timestamp: string;
  author: string;
  text: string;
}

export interface CounsellorCase {
  id: string;
  case_id: string;
  codeword: string;
  triage_priority: "P1 - Immediate" | "P2 - Within 2h" | "P3 - Routine";
  status: "new" | "contacted" | "in_support" | "resolved";
  distress_trajectory: { date: string; score: number; event?: string }[];
  fieldNotes: CaseNote[];
  signals: string[];
  summary: string;
  last_interaction: string;
  created_at: string;
  latest_checkin?: CheckInEntry;
  latest_source?: "chat" | "questionnaire" | "intake";
  share_personal_info?: boolean;
  victim_profile?: {
    name?: string;
    email?: string;
    phone?: string;
  };
  interaction_history?: VictimHistoryItem[];
  ml_scores?: {
    sentiment_label: "LOW" | "MODERATE" | "HIGH";
    sentiment_score: number;
    threat_flag: boolean;
    threat_prob: number;
    voice_stress_score?: number;
    voice_label?: "STRESSED" | "NOT_STRESSED";
    has_voice_recording?: boolean;
    composite_score: number;
    confidence: number;
    trend_flag: "ESCALATING" | "STABLE";
  };
}

export interface DecisionTrace {
  thread_id: string;
  case_id: string;
  decision: {
    route: "crisis" | "escalate" | "routine";
    policy_version: string;
    reasons: string[];
  };
  fusion: {
    confidence: number;
    top_signals: string[];
  };
  errors: string[];
  victim_text?: string;
}

const STORAGE_KEYS = {
  CHECKINS: "sahayak_checkins",
  REQUESTS: "sahayak_requests",
  ALERTS: "sahayak_alerts",
  CASES: "sahayak_cases",
  ACTIVE_CODEWORD: "sahayak_active_codeword",
  ROLE: "sahayak_role",
  TRACES: "sahayak_traces",
};

export function notifyStoreChange(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("sahayak_store_updated"));
  window.dispatchEvent(new Event("storage"));
}

export function subscribeToStore(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const handler = () => callback();
  window.addEventListener("sahayak_store_updated", handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener("sahayak_store_updated", handler);
    window.removeEventListener("storage", handler);
  };
}

// Natural evocative codeword generator
const ADJECTIVES = ["quiet", "amber", "gentle", "misty", "calm", "river", "silver", "forest", "cedar", "warm"];
const NOUNS = ["river", "valley", "harbor", "willow", "meadow", "lantern", "pebble", "sparrow", "branch", "path"];

export function generateCodeword(): string {
  const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
  const num = Math.floor(Math.random() * 89 + 10);
  return `${adj}-${noun}-${num}`;
}

// Check-ins
export function getCheckIns(): CheckInEntry[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEYS.CHECKINS);
  if (!raw) return seedInitialCheckIns();
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveCheckIn(entry: Omit<CheckInEntry, "id" | "createdAt">): CheckInEntry {
  const all = getCheckIns();
  const newEntry: CheckInEntry = {
    ...entry,
    id: `chk_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    createdAt: Date.now(),
  };
  const updated = [newEntry, ...all];
  localStorage.setItem(STORAGE_KEYS.CHECKINS, JSON.stringify(updated));
  notifyStoreChange();
  return newEntry;
}

export function deleteCheckIn(id: string): void {
  const all = getCheckIns();
  const filtered = all.filter((c) => c.id !== id);
  localStorage.setItem(STORAGE_KEYS.CHECKINS, JSON.stringify(filtered));
  notifyStoreChange();
}

// Help Requests
export function getHelpRequests(): HelpRequest[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEYS.REQUESTS);
  if (!raw) return seedInitialRequests();
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveHelpRequest(req: Omit<HelpRequest, "id" | "createdAt">): HelpRequest {
  const all = getHelpRequests();
  const newReq: HelpRequest = {
    ...req,
    id: `req_${Date.now()}`,
    createdAt: new Date().toISOString(),
  };
  const updated = [newReq, ...all];
  localStorage.setItem(STORAGE_KEYS.REQUESTS, JSON.stringify(updated));
  localStorage.setItem(STORAGE_KEYS.ACTIVE_CODEWORD, req.codeword);

  // Auto-sync into counsellor case files for seamless live demo!
  syncNewRequestToCases(newReq);
  notifyStoreChange();

  return newReq;
}

export function getActiveCodeword(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEYS.ACTIVE_CODEWORD);
}

export function setActiveCodeword(code: string): void {
  localStorage.setItem(STORAGE_KEYS.ACTIVE_CODEWORD, code);
}

export interface VictimSharePreference {
  share: boolean;
  name?: string;
  email?: string;
  phone?: string;
}

export function getVictimSharePreference(): VictimSharePreference {
  if (typeof window === "undefined") return { share: false };
  try {
    const raw = localStorage.getItem("sahayak_victim_share_preference");
    if (raw) return JSON.parse(raw);
  } catch {}
  return { share: false };
}

export function setVictimSharePreference(pref: VictimSharePreference): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("sahayak_victim_share_preference", JSON.stringify(pref));
  notifyStoreChange();
}

export interface AuthUser {
  user_id: string;
  email: string;
  name: string;
  role: "victim" | "counsellor" | "admin";
  phone?: string;
  codeword?: string;
  share_personal_info?: boolean;
}

export function getCurrentUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("sahayak_auth_user");
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

export function logoutUser(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("sahayak_access_token");
  localStorage.removeItem("sahayak_auth_role");
  localStorage.removeItem("sahayak_auth_user");
  localStorage.removeItem(STORAGE_KEYS.ACTIVE_CODEWORD);
  notifyStoreChange();
}

export function syncVictimAccountAndCase(info: {
  email: string;
  name: string;
  phone?: string;
  sharePersonalInfo: boolean;
  referralId?: string;
  user_id: string;
}): string {
  if (typeof window === "undefined") return "";

  const normEmail = info.email.trim().toLowerCase();
  // Maintain persistent codeword per victim account
  let cw = localStorage.getItem(`sahayak_user_codeword_${normEmail}`);
  if (!cw) {
    cw = info.referralId ? info.referralId.toLowerCase() : generateCodeword();
    localStorage.setItem(`sahayak_user_codeword_${normEmail}`, cw);
  }

  // Update active codeword & share preference
  setActiveCodeword(cw);
  setVictimSharePreference({
    share: info.sharePersonalInfo,
    name: info.sharePersonalInfo ? info.name : undefined,
    email: info.sharePersonalInfo ? info.email : undefined,
    phone: info.sharePersonalInfo ? info.phone : undefined,
  });

  // Save auth user object with codeword and explicit share preference
  const authUser: AuthUser = {
    user_id: info.user_id,
    email: info.email,
    name: info.name,
    role: "victim",
    phone: info.phone,
    codeword: cw,
    share_personal_info: info.sharePersonalInfo,
  };
  localStorage.setItem("sahayak_auth_user", JSON.stringify(authUser));

  // Sync with CounsellorCase immediately so counsellor views live status
  const cases = getCases();
  let targetCase = cases.find((c) => c.codeword === cw || c.case_id === cw);
  let updatedCases: CounsellorCase[];

  if (targetCase) {
    updatedCases = cases.map((c) => {
      if (c.id === targetCase!.id) {
        return {
          ...c,
          share_personal_info: info.sharePersonalInfo,
          victim_profile: info.sharePersonalInfo
            ? { name: info.name, email: info.email, phone: info.phone }
            : undefined,
          signals: Array.from(new Set([
            ...c.signals.filter((s) => s !== "Strict Anonymous Shield" && s !== "Personal Info Disclosed"),
            info.sharePersonalInfo ? "Personal Info Disclosed" : "Strict Anonymous Shield",
          ])),
        };
      }
      return c;
    });
  } else {
    const newCaseId = `case-${Math.floor(1000 + Math.random() * 9000)}`;
    const createdCase: CounsellorCase = {
      id: newCaseId,
      case_id: newCaseId,
      codeword: cw,
      triage_priority: "P3 - Routine",
      status: "new",
      share_personal_info: info.sharePersonalInfo,
      victim_profile: info.sharePersonalInfo
        ? { name: info.name, email: info.email, phone: info.phone }
        : undefined,
      distress_trajectory: [{ date: "Intake", score: 0.35 }],
      fieldNotes: [],
      interaction_history: [],
      signals: [info.sharePersonalInfo ? "Personal Info Disclosed" : "Strict Anonymous Shield", "PWA Secure"],
      summary: "",
      last_interaction: "Just now",
      created_at: new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
    };
    updatedCases = [createdCase, ...cases];
  }

  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(updatedCases));
  notifyStoreChange();
  return cw;
}

// Triage Alerts
export function getAlerts(): TriageAlert[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEYS.ALERTS);
  if (!raw) return seedInitialAlerts();
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function decideAlert(alertId: string, approved: boolean, note?: string): void {
  const alerts = getAlerts();
  const updated = alerts.map((a) => {
    if (a.alert_id === alertId) {
      return {
        ...a,
        decision_status: approved ? ("approved" as const) : ("rejected" as const),
        counsellor_note: note || (approved ? "Approved by counsellor on duty" : "De-escalated to routine checkin"),
      };
    }
    return a;
  });
  localStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(updated));
  notifyStoreChange();
}

// Counsellor Cases
export function getCases(): CounsellorCase[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEYS.CASES);
  if (!raw) return seedInitialCases();
  try {
    const parsed: CounsellorCase[] = JSON.parse(raw);
    // Sanitize: strictly retain clinician notes in fieldNotes (strip out any victim chat/questionnaire strings)
    return parsed.map((c) => ({
      ...c,
      fieldNotes: (c.fieldNotes || []).filter((n) => !n.author.toLowerCase().includes("victim")),
    }));
  } catch {
    return [];
  }
}

export function getCaseById(id: string): CounsellorCase | undefined {
  const cases = getCases();
  return cases.find((c) => c.id === id || c.case_id === id || c.codeword === id);
}

export function updateCaseStatus(id: string, status: CounsellorCase["status"]): void {
  const cases = getCases();
  const updated = cases.map((c) => {
    if (c.id === id || c.case_id === id) {
      return { ...c, status, last_interaction: "Just now" };
    }
    return c;
  });
  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(updated));

  // Sync to requests if applicable
  const reqs = getHelpRequests();
  const updatedReqs = reqs.map((r) => (r.id === id || r.codeword === id ? { ...r, status } : r));
  localStorage.setItem(STORAGE_KEYS.REQUESTS, JSON.stringify(updatedReqs));
  notifyStoreChange();
}

export function addCaseNote(id: string, noteText: string, author = "Dr. Ananya Roy"): void {
  const cases = getCases();
  const newNote: CaseNote = {
    id: `note_${Date.now()}`,
    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    author,
    text: noteText,
  };
  const updated = cases.map((c) => {
    if (c.id === id || c.case_id === id) {
      return {
        ...c,
        fieldNotes: [newNote, ...c.fieldNotes],
        last_interaction: "Just now",
      };
    }
    return c;
  });
  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(updated));
  notifyStoreChange();
}

export function saveDecisionTrace(trace: DecisionTrace): void {
  if (typeof window === "undefined") return;
  const raw = localStorage.getItem(STORAGE_KEYS.TRACES);
  let traces: Record<string, DecisionTrace> = {};
  if (raw) {
    try {
      traces = JSON.parse(raw);
    } catch {
      traces = {};
    }
  }
  traces[trace.thread_id] = trace;
  localStorage.setItem(STORAGE_KEYS.TRACES, JSON.stringify(traces));
  notifyStoreChange();
}

// Decision Trace audit retrieval
export function getDecisionTrace(threadId: string): DecisionTrace {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(STORAGE_KEYS.TRACES);
    if (raw) {
      try {
        const stored = JSON.parse(raw);
        if (stored[threadId]) return stored[threadId];
      } catch (e) {
        console.error("Failed to parse stored traces", e);
      }
    }
  }

  const traces: Record<string, DecisionTrace> = {
    "thread-8492": {
      thread_id: "thread-8492",
      case_id: "case-9412",
      decision: {
        route: "crisis",
        policy_version: "v2.4.1-safety",
        reasons: [
          "Urgent crisis keywords detected in interaction sequence",
          "Distress slope delta exceeded +0.48 across 48h check-in ladder",
          "Consent scope verified: CHAT_ANALYSIS and ESCALATION_LADDER active",
          "Multi-signal fusion triggered priority override",
        ],
      },
      fusion: {
        confidence: 0.94,
        top_signals: ["lexical_urgency (0.96)", "missed_checkin_weight (0.88)", "sleep_deficit (0.82)"],
      },
      errors: [],
      victim_text: "I don't think I can make it through tonight. Please help me before I do something to myself.",
    },
    "thread-6218": {
      thread_id: "thread-6218",
      case_id: "case-8820",
      decision: {
        route: "escalate",
        policy_version: "v2.4.1-safety",
        reasons: [
          "Sustained 4-day isolation indicators",
          "Victim requested quiet callback window between 6 PM - 8 PM",
          "No immediate crisis language, but safety ladder recommended review",
        ],
      },
      fusion: {
        confidence: 0.86,
        top_signals: ["callback_urgency (0.89)", "sentiment_dampening (0.84)"],
      },
      errors: ["Voice signal telemetry unavailable (opted out by user)"],
      victim_text: "Feeling so isolated and scared to step out of the house. Need a quiet callback.",
    },
  };

  return (
    traces[threadId] || {
      thread_id: threadId,
      case_id: "case-live",
      decision: {
        route: "routine",
        policy_version: "v2.4.1-safety",
        reasons: ["Standard wellbeing checkin within normal threshold"],
      },
      fusion: {
        confidence: 0.78,
        top_signals: ["baseline_stability (0.80)"],
      },
      errors: [],
      victim_text: "Today was quiet. Walking by the river helped a lot.",
    }
  );
}

// Safety-critical Quick Exit
export function executeQuickExit(): void {
  try {
    localStorage.clear();
    sessionStorage.clear();
    // Clear cookies
    if (typeof document !== "undefined") {
      document.cookie.split(";").forEach((c) => {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
    }
  } catch (err) {
    console.error("Quick exit error:", err);
  }
  // Immediately navigate to innocent search page
  window.location.replace("https://www.google.com/search?q=weather+today");
}

export interface VictimInteractionScores {
  sentiment: {
    label: "LOW" | "MODERATE" | "HIGH";
    sentiment_score: number;
    confidence: number;
    model_version?: string;
  };
  threat: {
    threat_flag: boolean;
    prob: number;
    confidence: number;
    model_version?: string;
  };
  fusion?: {
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
  };
  composite_score?: number;
}

export function recordVictimInteraction(
  userText: string,
  scores: VictimInteractionScores
): { caseId: string; threadId: string; alertId?: string } {
  const cases = getCases();
  const currentUser = getCurrentUser();
  let codeword = currentUser?.codeword || getActiveCodeword();
  if (!codeword) {
    codeword = generateCodeword();
    setActiveCodeword(codeword);
  }

  const threadId = `thread-${Math.floor(1000 + Math.random() * 9000)}`;
  const nowTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const isThreat = scores.threat.threat_flag || scores.threat.prob >= 0.70;
  const isCritical =
    scores.fusion?.label === "CRITICAL" ||
    isThreat ||
    (scores.fusion?.triggers && scores.fusion.triggers.includes("threat_force"));
  const isHighRisk =
    isCritical ||
    scores.fusion?.label === "HIGH" ||
    scores.sentiment.sentiment_score >= 0.65;

  const compositeScore =
    scores.fusion?.composite_score ??
    scores.composite_score ??
    Number(((scores.sentiment.sentiment_score * 0.262) + (scores.threat.prob * 0.590) + (0.35 * 0.148)).toFixed(2));

  const confidenceScore =
    scores.fusion?.confidence ??
    Number(((scores.sentiment.confidence + scores.threat.confidence) / 2).toFixed(2));

  const sharePref = getVictimSharePreference();

  const historyItem: VictimHistoryItem = {
    id: `vhist_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    timestamp: `${new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" })} ${nowTime}`,
    text: userText,
    source: "chat",
    risk_level: isCritical ? "CRITICAL" : isHighRisk ? "HIGH" : "MODERATE",
    details: `MuRIL: ${scores.sentiment.label} (${(scores.sentiment.sentiment_score * 100).toFixed(0)}%) · Threat: ${scores.threat.threat_flag ? "FLAGGED" : "CLEAR"}`,
  };

  // Find existing case or create a new one
  let targetCase = cases.find((c) => c.codeword === codeword || c.case_id === codeword);
  let updatedCases: CounsellorCase[];

  const newNote: CaseNote = {
    id: `fn_msg_${Date.now()}`,
    timestamp: nowTime,
    author: isCritical ? "VICTIM (CRITICAL FUSION ALERT)" : "Victim (Live Chat)",
    text: userText,
  };

  const trendFlag = isCritical ? "ESCALATING" : isHighRisk ? "ESCALATING" : "STABLE";
  const priorityStr = isCritical
    ? "P1 - Immediate"
    : isHighRisk
    ? "P2 - Within 2h"
    : "P3 - Routine";

  if (targetCase) {
    const newTraj = [
      ...targetCase.distress_trajectory,
      {
        date: "Today " + nowTime,
        score: Number(compositeScore.toFixed(2)),
        event: isCritical ? "Crisis Fusion Warning" : "Live chat interaction",
      },
    ];

    const currentHistory = targetCase.interaction_history || [];
    const updatedHistory = [...currentHistory, historyItem];

    updatedCases = cases.map((c) => {
      if (c.id === targetCase!.id) {
        return {
          ...c,
          summary: userText.length > 120 ? userText.slice(0, 117) + "..." : userText,
          last_interaction: "Just now",
          triage_priority: priorityStr,
          distress_trajectory: newTraj,
          fieldNotes: c.fieldNotes,
          interaction_history: updatedHistory,
          share_personal_info: sharePref.share,
          victim_profile: sharePref.share
            ? (c.victim_profile || (sharePref.name ? { name: sharePref.name, email: sharePref.email, phone: sharePref.phone } : undefined))
            : undefined,
          status: c.status === "resolved" ? "in_support" : c.status, // Reopen case if closed
          signals: Array.from(new Set([
            ...c.signals,
            `Fusion: ${scores.fusion?.label || (isCritical ? "CRITICAL" : "ELEVATED")}`,
            `Distress: ${scores.sentiment.label}`,
            scores.threat.threat_flag ? "Threat Flagged" : "Threat Clear",
            "Live Sanctuary Stream",
          ])),
          ml_scores: {
            sentiment_label: scores.sentiment.label,
            sentiment_score: Number(scores.sentiment.sentiment_score.toFixed(2)),
            threat_flag: scores.threat.threat_flag,
            threat_prob: Number(scores.threat.prob.toFixed(2)),
            voice_stress_score: c.ml_scores?.has_voice_recording ? c.ml_scores.voice_stress_score : undefined,
            voice_label: c.ml_scores?.has_voice_recording ? c.ml_scores.voice_label : undefined,
            has_voice_recording: c.ml_scores?.has_voice_recording || false,
            composite_score: Number(compositeScore.toFixed(2)),
            confidence: confidenceScore,
            trend_flag: trendFlag,
          },
        };
      }
      return c;
    });
  } else {
    const newCaseId = `case-${Math.floor(1000 + Math.random() * 9000)}`;
    const createdCase: CounsellorCase = {
      id: newCaseId,
      case_id: newCaseId,
      codeword,
      triage_priority: priorityStr,
      status: "new",
      distress_trajectory: [
        { date: "Intake", score: 0.35 },
        {
          date: "Today " + nowTime,
          score: Number(compositeScore.toFixed(2)),
          event: isCritical ? "Urgent Crisis Flagged" : "Live Chat Interaction",
        },
      ],
      fieldNotes: [],
      interaction_history: [historyItem],
      share_personal_info: sharePref.share,
      victim_profile: sharePref.share ? { name: sharePref.name, email: sharePref.email, phone: sharePref.phone } : undefined,
      signals: [
        `Fusion: ${scores.fusion?.label || (isCritical ? "CRITICAL" : "ELEVATED")}`,
        `Distress: ${scores.sentiment.label}`,
        scores.threat.threat_flag ? "Threat Flagged" : "Threat Clear",
        "Sanctuary Chat",
      ],
      summary: userText.length > 120 ? userText.slice(0, 117) + "..." : userText,
      last_interaction: "Just now",
      created_at: new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      ml_scores: {
        sentiment_label: scores.sentiment.label,
        sentiment_score: Number(scores.sentiment.sentiment_score.toFixed(2)),
        threat_flag: scores.threat.threat_flag,
        threat_prob: Number(scores.threat.prob.toFixed(2)),
        has_voice_recording: false,
        composite_score: Number(compositeScore.toFixed(2)),
        confidence: confidenceScore,
        trend_flag: trendFlag,
      },
    };
    targetCase = createdCase;
    updatedCases = [createdCase, ...cases];
  }

  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(updatedCases));

  let alertId: string | undefined = undefined;

  // If elevated or critical risk, automatically inject into Triage Alert Queue and generate Decision Trace!
  if (isHighRisk || isCritical) {
    alertId = `alt-${Math.floor(1000 + Math.random() * 9000)}`;
    const riskLevel = isCritical ? "CRITICAL" : "HIGH";

    const reasons: string[] = [];
    if (scores.threat.threat_flag || scores.threat.prob >= 0.70) {
      reasons.push(`🚨 Threat classifier flagged high danger (P=${(scores.threat.prob * 100).toFixed(0)}%)`);
    }
    if (scores.fusion?.triggers && scores.fusion.triggers.includes("threat_force")) {
      reasons.push(`⚡ Bayesian Fusion Trigger: threat_force override engaged (risk floored at 0.80)`);
    }
    if (scores.sentiment.sentiment_score >= 0.65) {
      reasons.push(`Distress indicator elevated (MuRIL score ${(scores.sentiment.sentiment_score * 100).toFixed(0)}%)`);
    }
    reasons.push(`Victim snippet: "${userText.slice(0, 85)}${userText.length > 85 ? "..." : ""}"`);
    reasons.push(`Safety protocol: human counsellor review and active response required`);

    const newAlert: TriageAlert = {
      alert_id: alertId,
      case_id: targetCase.case_id,
      thread_id: threadId,
      risk_level: riskLevel,
      composite_score: Number(compositeScore.toFixed(2)),
      confidence: confidenceScore,
      triage_priority_score: Math.round(compositeScore * 100),
      raised_at: "Just now",
      decision_status: "pending",
      reasons,
      channel: "pwa_chat",
      victim_text: userText,
      victim_info: {
        codeword: targetCase.codeword,
        share_personal_info: !!(targetCase.share_personal_info ?? sharePref.share),
        name: (targetCase.victim_profile?.name || sharePref.name),
        email: (targetCase.victim_profile?.email || sharePref.email),
        latest_mood: targetCase.latest_checkin?.moodLabel,
        latest_sleep: targetCase.latest_checkin ? `${targetCase.latest_checkin.sleepHours}h (${targetCase.latest_checkin.sleepQuality})` : undefined,
        history_count: ((targetCase.interaction_history || []).length) + 1,
      },
      history: [...(targetCase.interaction_history || []), historyItem],
    };

    const existingAlerts = getAlerts();
    localStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify([newAlert, ...existingAlerts]));

    // Generate matching Explainable Decision Trace for the audit trail
    const traceSignals = scores.fusion?.top_signals?.length
      ? scores.fusion.top_signals.map((s) => {
          if (s === "threat") return `threat_detector (${(scores.threat.prob * 100).toFixed(0)}%)`;
          if (s === "sentiment") return `muril_distress (${(scores.sentiment.sentiment_score * 100).toFixed(0)}%)`;
          if (s === "voice_stress") return `voice_stress_sensor (35%)`;
          return s;
        })
      : [
          `muril_distress (${(scores.sentiment.sentiment_score * 100).toFixed(0)}%)`,
          `threat_detector (${(scores.threat.prob * 100).toFixed(0)}%)`,
          `chat_sentiment (${scores.sentiment.label})`,
        ];

    const trace: DecisionTrace = {
      thread_id: threadId,
      case_id: targetCase.case_id,
      decision: {
        route: isCritical ? "crisis" : "escalate",
        policy_version: "v2.4.1-safety",
        reasons,
      },
      fusion: {
        confidence: confidenceScore,
        top_signals: traceSignals,
      },
      errors: [],
      victim_text: userText,
    };
    saveDecisionTrace(trace);
  }

  notifyStoreChange();
  return { caseId: targetCase.case_id, threadId, alertId };
}

export function recordVictimQuestionnaire(entry: CheckInEntry): void {
  const cases = getCases();
  let codeword = getActiveCodeword();
  if (!codeword) {
    codeword = generateCodeword();
    setActiveCodeword(codeword);
  }

  const nowTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // Map mood (1..5) and sleep metrics to latent distress index
  // Mood 1 (Fragile) -> 0.88, Mood 2 (Heavy) -> 0.70, Mood 3 (Steady) -> 0.48, Mood 4 (Grounded) -> 0.28, Mood 5 (Light) -> 0.12
  const baseDistress = entry.mood === 1 ? 0.88 : entry.mood === 2 ? 0.70 : entry.mood === 3 ? 0.48 : entry.mood === 4 ? 0.28 : 0.12;
  const sleepPenalty = entry.sleepHours <= 4 ? 0.08 : entry.sleepHours <= 5.5 ? 0.04 : 0;
  const computedDistress = Math.min(0.98, Math.max(0.08, baseDistress + sleepPenalty));

  const isCritical = entry.mood === 1 && (entry.sleepHours <= 4 || (entry.reflection && /kill|die|suicide|hurt|threat|follow|harm/i.test(entry.reflection)));
  const isElevated = isCritical || entry.mood <= 2 || entry.sleepHours <= 4;

  const noteText = `[Daily Questionnaire Completed] Mood: ${entry.moodLabel} (${entry.mood}/5) · Sleep: ${entry.sleepHours}h (${entry.sleepQuality}) · Feelings: [${entry.feelings.join(", ")}]${entry.reflection ? ` · Written Reflection: "${entry.reflection}"` : ""}`;

  const newNote: CaseNote = {
    id: `fn_chk_${Date.now()}`,
    timestamp: nowTime,
    author: isCritical ? "VICTIM (CRITICAL QUESTIONNAIRE)" : "Victim (Check-in Questionnaire)",
    text: noteText,
  };

  const priorityStr = isCritical ? "P1 - Immediate" : isElevated ? "P2 - Within 2h" : "P3 - Routine";

  let targetCase = cases.find((c) => c.codeword === codeword || c.case_id === codeword);
  let updatedCases: CounsellorCase[];

  const summaryText = `[Questionnaire] Felt ${entry.moodLabel} (${entry.sleepHours}h rest)${entry.reflection ? `: "${entry.reflection}"` : ` with feelings: ${entry.feelings.slice(0, 3).join(", ")}`}`;

  const sharePref = getVictimSharePreference();

  const qHistoryItem: VictimHistoryItem = {
    id: `vhist_q_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    timestamp: `${new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" })} ${nowTime}`,
    text: `Felt ${entry.moodLabel} (${entry.mood}/5) · Rest: ${entry.sleepHours}h (${entry.sleepQuality})${entry.reflection ? ` · "${entry.reflection}"` : ""}`,
    source: "questionnaire",
    risk_level: isCritical ? "CRITICAL" : isElevated ? "HIGH" : "LOW",
    details: `Feelings: ${entry.feelings.join(", ")}`,
  };

  if (targetCase) {
    const newTraj = [
      ...targetCase.distress_trajectory,
      {
        date: "Today " + nowTime,
        score: Number(computedDistress.toFixed(2)),
        event: `Questionnaire (${entry.moodLabel})`,
      },
    ];

    const currentHistory = targetCase.interaction_history || [];
    const updatedHistory = [...currentHistory, qHistoryItem];

    updatedCases = cases.map((c) => {
      if (c.id === targetCase!.id) {
        return {
          ...c,
          summary: summaryText.length > 120 ? summaryText.slice(0, 117) + "..." : summaryText,
          last_interaction: "Just now",
          triage_priority: isCritical ? "P1 - Immediate" : isElevated && !c.triage_priority.startsWith("P1") ? "P2 - Within 2h" : c.triage_priority,
          distress_trajectory: newTraj,
          fieldNotes: c.fieldNotes,
          interaction_history: updatedHistory,
          share_personal_info: sharePref.share,
          victim_profile: sharePref.share
            ? (c.victim_profile || (sharePref.name ? { name: sharePref.name, email: sharePref.email, phone: sharePref.phone } : undefined))
            : undefined,
          latest_checkin: entry,
          latest_source: "questionnaire" as const,
          status: c.status === "resolved" ? "in_support" : c.status,
          signals: Array.from(new Set([
            ...c.signals,
            `Mood: ${entry.moodLabel}`,
            `Sleep: ${entry.sleepHours}h (${entry.sleepQuality})`,
            ...entry.feelings.slice(0, 2),
            "Questionnaire Active",
          ])),
          ml_scores: {
            sentiment_label: computedDistress >= 0.7 ? "HIGH" : computedDistress >= 0.4 ? "MODERATE" : "LOW",
            sentiment_score: Number(computedDistress.toFixed(2)),
            threat_flag: c.ml_scores?.threat_flag || Boolean(entry.reflection && /follow|threat|kill|hurt/i.test(entry.reflection)),
            threat_prob: c.ml_scores?.threat_prob || 0.12,
            voice_stress_score: c.ml_scores?.has_voice_recording ? c.ml_scores.voice_stress_score : undefined,
            voice_label: c.ml_scores?.has_voice_recording ? c.ml_scores.voice_label : undefined,
            has_voice_recording: c.ml_scores?.has_voice_recording || false,
            composite_score: Number(((computedDistress * 0.5) + ((c.ml_scores?.threat_prob || 0.12) * 0.5)).toFixed(2)),
            confidence: 0.88,
            trend_flag: isElevated ? "ESCALATING" : "STABLE",
          },
        };
      }
      return c;
    });
  } else {
    const newCaseId = `case-${Math.floor(1000 + Math.random() * 9000)}`;
    const createdCase: CounsellorCase = {
      id: newCaseId,
      case_id: newCaseId,
      codeword,
      triage_priority: priorityStr,
      status: "new",
      distress_trajectory: [
        { date: "Intake", score: 0.35 },
        { date: "Today " + nowTime, score: Number(computedDistress.toFixed(2)), event: `Questionnaire (${entry.moodLabel})` },
      ],
      fieldNotes: [],
      interaction_history: [qHistoryItem],
      share_personal_info: sharePref.share,
      victim_profile: sharePref.share ? { name: sharePref.name, email: sharePref.email, phone: sharePref.phone } : undefined,
      signals: [
        `Mood: ${entry.moodLabel}`,
        `Sleep: ${entry.sleepHours}h (${entry.sleepQuality})`,
        ...entry.feelings.slice(0, 2),
        "Daily Check-in",
      ],
      summary: summaryText.length > 120 ? summaryText.slice(0, 117) + "..." : summaryText,
      last_interaction: "Just now",
      created_at: new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      latest_checkin: entry,
      latest_source: "questionnaire",
      ml_scores: {
        sentiment_label: computedDistress >= 0.7 ? "HIGH" : computedDistress >= 0.4 ? "MODERATE" : "LOW",
        sentiment_score: Number(computedDistress.toFixed(2)),
        threat_flag: Boolean(entry.reflection && /follow|threat|kill|hurt/i.test(entry.reflection)),
        threat_prob: 0.12,
        has_voice_recording: false,
        composite_score: Number(computedDistress.toFixed(2)),
        confidence: 0.88,
        trend_flag: isElevated ? "ESCALATING" : "STABLE",
      },
    };
    targetCase = createdCase;
    updatedCases = [createdCase, ...cases];
  }

  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(updatedCases));

  if (isElevated) {
    const alertId = `alt-${Math.floor(1000 + Math.random() * 9000)}`;
    const newAlert: TriageAlert = {
      alert_id: alertId,
      case_id: targetCase.case_id,
      thread_id: `thread-${Math.floor(1000 + Math.random() * 9000)}`,
      risk_level: isCritical ? "CRITICAL" : "HIGH",
      composite_score: Number(computedDistress.toFixed(2)),
      confidence: 0.88,
      triage_priority_score: Math.round(computedDistress * 100),
      raised_at: "Just now",
      decision_status: "pending",
      reasons: [
        `📋 Questionnaire Indicator: Victim reported state '${entry.moodLabel}' (Level ${entry.mood}/5)`,
        `Rest telemetry: ${entry.sleepHours}h (${entry.sleepQuality})${entry.sleepHours <= 4 ? " — severe rest deprivation" : ""}`,
        `Feelings flagged: ${entry.feelings.join(", ")}`,
        ...(entry.reflection ? [`Victim reflection: "${entry.reflection.slice(0, 80)}..."`] : []),
      ],
      channel: "questionnaire_checkin",
      victim_text: entry.reflection || `Daily check-in: Mood ${entry.moodLabel} (${entry.mood}/5), Rest: ${entry.sleepHours}h, Feelings: ${entry.feelings.join(", ")}`,
      victim_info: {
        codeword: targetCase.codeword,
        share_personal_info: !!(targetCase.share_personal_info ?? sharePref.share),
        name: (targetCase.victim_profile?.name || sharePref.name),
        email: (targetCase.victim_profile?.email || sharePref.email),
        latest_mood: entry.moodLabel,
        latest_sleep: `${entry.sleepHours}h (${entry.sleepQuality})`,
        history_count: ((targetCase.interaction_history || []).length) + 1,
      },
      history: [...(targetCase.interaction_history || []), qHistoryItem],
    };
    const existingAlerts = getAlerts();
    localStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify([newAlert, ...existingAlerts]));

    // Generate explainable decision trace for questionnaire alert
    const qTrace: DecisionTrace = {
      thread_id: newAlert.thread_id,
      case_id: targetCase.case_id,
      decision: {
        route: isCritical ? "crisis" : "escalate",
        policy_version: "v2.4.1-safety",
        reasons: newAlert.reasons,
      },
      fusion: {
        confidence: 0.88,
        top_signals: [
          `questionnaire_distress (${(computedDistress * 100).toFixed(0)}%)`,
          `rest_deprivation (${entry.sleepHours}h)`,
          `mood_rating (${entry.mood}/5)`,
        ],
      },
      errors: [],
      victim_text: newAlert.victim_text,
    };
    saveDecisionTrace(qTrace);
  }

  notifyStoreChange();
}

// Sync helper
function syncNewRequestToCases(req: HelpRequest) {
  const cases = getCases();
  const newCase: CounsellorCase = {
    id: req.id,
    case_id: req.id,
    codeword: req.codeword,
    triage_priority: req.supportType === "crisis" ? "P1 - Immediate" : "P2 - Within 2h",
    status: "new",
    distress_trajectory: [
      { date: "Day 1", score: 0.4 },
      { date: "Day 2", score: 0.6 },
      { date: "Today", score: req.supportType === "crisis" ? 0.92 : 0.65, event: "Requested Support" },
    ],
    fieldNotes: [
      {
        id: `fn_init_${Date.now()}`,
        timestamp: "Just now",
        author: "System Intake",
        text: `Confidential intake generated. Preferred contact: ${req.contactMethod}. Type: ${req.supportTypeLabel}.`,
      },
    ],
    signals: [
      req.supportTypeLabel,
      req.contactMethod === "callback" ? "Callback Window" : "In-App Only",
      "Consent active",
    ],
    summary: req.notes || "Victim requested steady human touchpoint through anonymous portal.",
    last_interaction: "Just now",
    created_at: new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
  };
  localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify([newCase, ...cases]));
}

// Initial Seeds for Hackathon Demo
function seedInitialCheckIns(): CheckInEntry[] {
  const today = new Date();
  const entries: CheckInEntry[] = [
    {
      id: "chk-1",
      date: new Date(today.getTime() - 86400000 * 4).toISOString().split("T")[0],
      mood: 2,
      moodLabel: "Heavy",
      sleepHours: 4.5,
      sleepQuality: "Restless",
      feelings: ["heavy", "exhausted", "foggy"],
      reflection: "Everything felt louder than usual. Took a long walk near the trees.",
      createdAt: today.getTime() - 86400000 * 4,
    },
    {
      id: "chk-2",
      date: new Date(today.getTime() - 86400000 * 3).toISOString().split("T")[0],
      mood: 3,
      moodLabel: "Steady",
      sleepHours: 6,
      sleepQuality: "Broken",
      feelings: ["steady", "quiet", "tender"],
      reflection: "Made tea and watched the rain for half an hour.",
      createdAt: today.getTime() - 86400000 * 3,
    },
    {
      id: "chk-3",
      date: new Date(today.getTime() - 86400000 * 2).toISOString().split("T")[0],
      mood: 3,
      moodLabel: "Steady",
      sleepHours: 6.5,
      sleepQuality: "Adequate",
      feelings: ["breathing", "patient"],
      reflection: "Remembered that feelings are weather. They come and pass.",
      createdAt: today.getTime() - 86400000 * 2,
    },
    {
      id: "chk-4",
      date: new Date(today.getTime() - 86400000 * 1).toISOString().split("T")[0],
      mood: 4,
      moodLabel: "Grounded",
      sleepHours: 7,
      sleepQuality: "Restful",
      feelings: ["grounded", "hopeful", "soft"],
      reflection: "Slept through the night without waking in panic.",
      createdAt: today.getTime() - 86400000 * 1,
    },
  ];
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEYS.CHECKINS, JSON.stringify(entries));
  }
  return entries;
}

function seedInitialRequests(): HelpRequest[] {
  const requests: HelpRequest[] = [
    {
      id: "req-1",
      codeword: "quiet-river-17",
      supportType: "emotional",
      supportTypeLabel: "Emotional Grounding",
      contactMethod: "in_app",
      consentScopes: {
        chatAnalysis: true,
        voiceSignals: false,
        emailCheckin: false,
        smsCheckin: false,
        escalationLadder: true,
      },
      status: "in_support",
      createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
      assignedCounsellor: "Dr. Ananya Roy",
    },
    {
      id: "req-2",
      codeword: "amber-meadow-42",
      supportType: "domestic",
      supportTypeLabel: "Confidential Safety Support",
      contactMethod: "callback",
      callbackWindow: "Evening 7:00 PM - 8:30 PM",
      notes: "Please do not mention Sahaara if someone else answers.",
      consentScopes: {
        chatAnalysis: true,
        voiceSignals: false,
        emailCheckin: false,
        smsCheckin: false,
        escalationLadder: true,
      },
      status: "contacted",
      createdAt: new Date(Date.now() - 86400000 * 1).toISOString(),
      assignedCounsellor: "M. Fernandes",
    },
  ];
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEYS.REQUESTS, JSON.stringify(requests));
  }
  return requests;
}

function seedInitialAlerts(): TriageAlert[] {
  const alerts: TriageAlert[] = [
    {
      alert_id: "alt-9041",
      case_id: "case-9412",
      thread_id: "thread-8492",
      risk_level: "CRITICAL",
      composite_score: 0.94,
      confidence: 0.91,
      triage_priority_score: 98,
      raised_at: "14 mins ago",
      decision_status: "pending",
      reasons: ["Critical distress spike", "Explicit suicidal ideation phrasing detected"],
      channel: "pwa_chat",
      victim_text: "I don't think I can make it through tonight. Please help me before I do something to myself.",
      victim_info: {
        codeword: "quiet-river-17",
        share_personal_info: true,
        name: "Maya S.",
        email: "maya.s@proton.me",
        latest_mood: "Fragile (1/5)",
        latest_sleep: "3.5h (Restless)",
        history_count: 3,
      },
      history: [
        {
          id: "vh_9041_1",
          timestamp: "Sep 7 19:40",
          text: "I am feeling so trapped, the shouting started again.",
          source: "chat",
          risk_level: "HIGH",
          details: "MuRIL: HIGH (88%)",
        },
        {
          id: "vh_9041_2",
          timestamp: "Sep 7 21:10",
          text: "Felt Fragile (1/5) · Rest: 3.5h (Restless) · Feelings: overwhelmed, terrified",
          source: "questionnaire",
          risk_level: "HIGH",
        },
        {
          id: "vh_9041_3",
          timestamp: "Sep 7 21:14",
          text: "I don't think I can make it through tonight. Please help me before I do something to myself.",
          source: "chat",
          risk_level: "CRITICAL",
          details: "Explicit crisis phrasing detected",
        },
      ],
    },
    {
      alert_id: "alt-8812",
      case_id: "case-8820",
      thread_id: "thread-6218",
      risk_level: "HIGH",
      composite_score: 0.78,
      confidence: 0.86,
      triage_priority_score: 82,
      raised_at: "48 mins ago",
      decision_status: "pending",
      reasons: ["Multiple missed check-in windows", "Escalation ladder step 2 reached"],
      channel: "checkin_ladder",
      victim_text: "Feeling so isolated and scared to step out of the house. Need a quiet callback.",
      victim_info: {
        codeword: "amber-meadow-42",
        share_personal_info: false,
        latest_mood: "Heavy (2/5)",
        latest_sleep: "4.5h (Broken)",
        history_count: 2,
      },
      history: [
        {
          id: "vh_8812_1",
          timestamp: "Sep 8 09:20",
          text: "Felt Heavy (2/5) · Rest: 4.5h · Missed morning safety ping",
          source: "questionnaire",
          risk_level: "HIGH",
        },
        {
          id: "vh_8812_2",
          timestamp: "Sep 8 10:12",
          text: "Feeling so isolated and scared to step out of the house. Need a quiet callback.",
          source: "chat",
          risk_level: "HIGH",
          details: "Safe window requested 7 PM",
        },
      ],
    },
    {
      alert_id: "alt-7193",
      case_id: "case-7731",
      thread_id: "thread-3301",
      risk_level: "MODERATE",
      composite_score: 0.58,
      confidence: 0.79,
      triage_priority_score: 61,
      raised_at: "2 hours ago",
      decision_status: "approved",
      counsellor_note: "Assigned to peer listener follow-up",
      reasons: ["Sleep deficit 4 consecutive days", "Gentle check-in recommended"],
      channel: "daily_checkin",
      victim_text: "Unable to sleep more than 3 hours every night. Head hurts constantly.",
      victim_info: {
        codeword: "misty-cedar-88",
        share_personal_info: false,
        latest_mood: "Steady (3/5)",
        latest_sleep: "3.0h (Broken)",
        history_count: 1,
      },
      history: [
        {
          id: "vh_7193_1",
          timestamp: "Sep 7 12:05",
          text: "Unable to sleep more than 3 hours every night. Head hurts constantly.",
          source: "chat",
          risk_level: "MODERATE",
        },
      ],
    },
  ];
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(alerts));
  }
  return alerts;
}

function seedInitialCases(): CounsellorCase[] {
  const cases: CounsellorCase[] = [
    {
      id: "case-9412",
      case_id: "case-9412",
      codeword: "quiet-river-17",
      triage_priority: "P1 - Immediate",
      status: "in_support",
      share_personal_info: true,
      victim_profile: {
        name: "Maya S.",
        email: "maya.s@proton.me",
        phone: "+91 98765 43210",
      },
      interaction_history: [
        {
          id: "ih-1",
          timestamp: "Sep 6, 14:20",
          text: "Felt Fragile (1/5) · Rest: 4h · Feelings: exhausted, isolated, scared",
          source: "questionnaire",
          risk_level: "HIGH",
        },
        {
          id: "ih-2",
          timestamp: "Sep 7, 19:40",
          text: "I am feeling so trapped, the shouting started again and they took the room keys.",
          source: "chat",
          risk_level: "HIGH",
          details: "MuRIL: HIGH (88%)",
        },
        {
          id: "ih-3",
          timestamp: "Sep 7, 21:14",
          text: "I don't think I can make it through tonight. Please help me before I do something to myself.",
          source: "chat",
          risk_level: "CRITICAL",
          details: "Crisis trigger overrides engaged",
        },
        {
          id: "ih-4",
          timestamp: "Sep 8, 18:35",
          text: "The breathing anchor helped steady my chest. Still frightened but grounded.",
          source: "chat",
          risk_level: "MODERATE",
        },
      ],
      distress_trajectory: [
        { date: "Sep 4", score: 0.35 },
        { date: "Sep 5", score: 0.42 },
        { date: "Sep 6", score: 0.58 },
        { date: "Sep 7", score: 0.85, event: "Crisis escalation" },
        { date: "Sep 8", score: 0.72, event: "Grounding session" },
        { date: "Today", score: 0.54, event: "De-escalating" },
      ],
      fieldNotes: [
        {
          id: "fn-1",
          timestamp: "Sep 8, 18:30",
          author: "Dr. Ananya Roy",
          text: "Held 20 min grounding over safe channel. Victim reported sensory anchors helped reduce racing thoughts.",
        },
        {
          id: "fn-2",
          timestamp: "Sep 7, 21:15",
          author: "M. Fernandes",
          text: "Initial triage approved after critical alert. Safety protocol confirmed.",
        },
      ],
      signals: ["Distress slope +0.48", "Sleep < 4h", "Consent active"],
      summary: "Undergoing guided unburdening. Receptive to grounding exercises; monitoring sleep recovery.",
      last_interaction: "35 mins ago",
      created_at: "Sep 4",
      ml_scores: {
        sentiment_label: "HIGH",
        sentiment_score: 0.87,
        threat_flag: true,
        threat_prob: 0.92,
        voice_stress_score: 0.81,
        voice_label: "STRESSED",
        composite_score: 0.87,
        confidence: 0.91,
        trend_flag: "ESCALATING",
      },
    },
    {
      id: "case-8820",
      case_id: "case-8820",
      codeword: "amber-meadow-42",
      triage_priority: "P2 - Within 2h",
      status: "contacted",
      distress_trajectory: [
        { date: "Sep 6", score: 0.52 },
        { date: "Sep 7", score: 0.65 },
        { date: "Sep 8", score: 0.74, event: "Requested callback" },
        { date: "Today", score: 0.68 },
      ],
      fieldNotes: [
        {
          id: "fn-3",
          timestamp: "Today, 10:15",
          author: "Dr. Ananya Roy",
          text: "Scheduled callback in requested evening window (7 PM). Pre-briefed domestic safety directory.",
        },
      ],
      signals: ["Domestic safety request", "Callback window set", "Strict discreet mode"],
      summary: "Discreet callback requested. Safe window established for 7:00 PM.",
      last_interaction: "1 hour ago",
      created_at: "Sep 6",
      ml_scores: {
        sentiment_label: "MODERATE",
        sentiment_score: 0.61,
        threat_flag: false,
        threat_prob: 0.38,
        voice_stress_score: 0.55,
        voice_label: "STRESSED",
        composite_score: 0.52,
        confidence: 0.86,
        trend_flag: "STABLE",
      },
    },
    {
      id: "case-7731",
      case_id: "case-7731",
      codeword: "misty-cedar-88",
      triage_priority: "P3 - Routine",
      status: "resolved",
      distress_trajectory: [
        { date: "Sep 1", score: 0.6 },
        { date: "Sep 3", score: 0.45 },
        { date: "Sep 5", score: 0.3 },
        { date: "Sep 7", score: 0.22, event: "Completed grounding cycle" },
      ],
      fieldNotes: [
        {
          id: "fn-4",
          timestamp: "Sep 7, 14:00",
          author: "Dr. Ananya Roy",
          text: "Successfully stabilized. Check-ins steady for 5 consecutive days. Case closed with open unburdening door.",
        },
      ],
      signals: ["Stable 5+ days", "Sleep 7h+", "Routine closed"],
      summary: "Successfully stabilized. Returning to self-guided check-ins.",
      last_interaction: "2 days ago",
      created_at: "Sep 1",
      ml_scores: {
        sentiment_label: "LOW",
        sentiment_score: 0.18,
        threat_flag: false,
        threat_prob: 0.04,
        voice_stress_score: 0.21,
        voice_label: "NOT_STRESSED",
        composite_score: 0.19,
        confidence: 0.94,
        trend_flag: "STABLE",
      },
    },

  ];
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEYS.CASES, JSON.stringify(cases));
  }
  return cases;
}
