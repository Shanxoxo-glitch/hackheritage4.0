import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getCheckIns, deleteCheckIn, subscribeToStore, CheckInEntry } from "@/lib/store";
import { ArrowLeft, Trash2, Calendar, Sparkles, Moon, Sun, Flower2, Plus, Mic, FileText, Activity, Shield, Camera } from "lucide-react";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [{ title: "Garden of Days — Sahayak" }],
  }),
  component: HistoryGardenPage,
});

export default function HistoryGardenPage() {
  const [entries, setEntries] = useState<CheckInEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<CheckInEntry | null>(null);

  useEffect(() => {
    const refresh = () => {
      const list = getCheckIns();
      setEntries(list);
      setSelectedEntry((curr) => {
        if (!curr && list.length > 0) return list[0];
        if (curr) {
          const matching = list.find((e) => e.id === curr.id);
          return matching || list[0] || null;
        }
        return null;
      });
    };

    refresh();
    const unsubscribe = subscribeToStore(refresh);
    return () => unsubscribe();
  }, []);

  const handleDelete = (id: string) => {
    deleteCheckIn(id);
    const updated = entries.filter((e) => e.id !== id);
    setEntries(updated);
    if (selectedEntry?.id === id) {
      setSelectedEntry(updated[0] || null);
    }
  };

  // Warm summary narrative
  const getWarmSummary = () => {
    if (entries.length === 0) return "A quiet soil ready for your first thought.";
    const recent = entries.slice(0, 5);
    const avgMood = recent.reduce((sum, e) => sum + e.mood, 0) / recent.length;
    if (avgMood >= 3.8) return "A gentler, grounded stretch. Notice the quiet light you've gathered.";
    if (avgMood >= 2.8) return "A steady rhythm. Navigating the waves with patience.";
    return "Carrying tender weight this week. Treat yourself with extra gentleness today.";
  };

  // Flower color/size mapping based on mood
  const getBloomDetails = (mood: number) => {
    switch (mood) {
      case 5:
        return { height: "h-36", color: "bg-sage text-forest", glow: "shadow-sage/40", petal: "☀️" };
      case 4:
        return { height: "h-32", color: "bg-forest/20 text-forest", glow: "shadow-forest/30", petal: "🌱" };
      case 3:
        return { height: "h-28", color: "bg-sage/40 text-sage-deep", glow: "shadow-sage/30", petal: "🍃" };
      case 2:
        return { height: "h-20", color: "bg-clay/20 text-clay", glow: "shadow-clay/30", petal: "🌧️" };
      case 1:
      default:
        return { height: "h-16", color: "bg-clay/30 text-clay-foreground", glow: "shadow-clay/40", petal: "💧" };
    }
  };

  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-6xl space-y-10">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-foreground/10 pb-6">
          <div className="space-y-1">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors mb-2"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Sanctuary</span>
            </Link>
            <h1 className="text-4xl md:text-5xl font-display">Your Garden of Days</h1>
            <p className="text-sm text-foreground/65 max-w-lg">{getWarmSummary()}</p>
          </div>

          <Link
            to="/checkin"
            className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-3 text-sm font-medium text-forest-foreground shadow-[var(--shadow-lift)] hover:bg-clay transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>Plant today's check-in</span>
          </Link>
        </div>

        {/* SHOWPIECE: Living Garden Visualization */}
        <div className="rounded-3xl border border-foreground/10 bg-card/60 p-6 md:p-8 backdrop-blur-sm shadow-[var(--shadow-soft)]">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2.5">
              <Flower2 className="h-5 w-5 text-clay" />
              <span className="font-display text-2xl">This Week's Flora</span>
            </div>
            <span className="text-xs text-foreground/50">Each bloom mirrors a day's feeling</span>
          </div>

          {entries.length === 0 ? (
            <div className="text-center py-16 space-y-3">
              <p className="font-display text-xl text-foreground/60">No blossoms planted yet</p>
              <Link to="/checkin" className="text-xs text-clay underline font-medium">
                Take your first 60-second check-in
              </Link>
            </div>
          ) : (
            <div className="relative pt-12 pb-6 border-b-2 border-forest/20 flex items-end justify-around gap-2 min-h-[220px]">
              {/* Garden Soil line */}
              <div className="absolute bottom-0 inset-x-0 h-1 bg-gradient-to-r from-clay/30 via-forest/30 to-sage/30 rounded-full" />

              {entries.slice(0, 7).reverse().map((item, idx) => {
                const bloom = getBloomDetails(item.mood);
                const isSelected = selectedEntry?.id === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedEntry(item)}
                    className="group flex flex-col items-center cursor-pointer transition-transform hover:-translate-y-1 focus:outline-none"
                  >
                    {/* Flower head */}
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center text-sm border shadow-sm transition-all animate-stem ${
                        bloom.color
                      } ${isSelected ? "ring-2 ring-clay scale-110" : "group-hover:scale-105"}`}
                    >
                      {bloom.petal}
                    </div>

                    {/* Stem */}
                    <div
                      className={`w-1 rounded-t-full bg-forest/40 transition-all duration-700 ${
                        bloom.height
                      } ${isSelected ? "bg-forest w-1.5" : "group-hover:bg-forest/70"}`}
                    />

                    {/* Date label under soil */}
                    <span className="mt-2 text-[10px] text-foreground/60 font-mono">
                      {new Date(item.date).toLocaleDateString("en-IN", {
                        weekday: "short",
                        day: "numeric",
                      })}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Two Columns: Month Calendar & Past Entries Detail */}
        <div className="grid md:grid-cols-12 gap-8">
          {/* Left Column: Entries List & Soft Calendar Dots */}
          <div className="md:col-span-6 space-y-4">
            <h2 className="font-display text-2xl flex items-center gap-2">
              <Calendar className="h-4 w-4 text-sage-deep" />
              <span>Past Days</span>
            </h2>

            <div className="space-y-2.5">
              {entries.map((entry) => {
                const isSelected = selectedEntry?.id === entry.id;
                return (
                  <div
                    key={entry.id}
                    onClick={() => setSelectedEntry(entry)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? "border-clay bg-card shadow-[var(--shadow-lift)]"
                        : "border-foreground/10 bg-card/40 hover:bg-card/70"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {/* Soft color dot */}
                      <span
                        className={`h-3 w-3 rounded-full ${
                          entry.mood >= 4 ? "bg-forest" : entry.mood === 3 ? "bg-sage" : "bg-clay"
                        }`}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-foreground">
                            {new Date(entry.date).toLocaleDateString("en-IN", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })}
                          </span>
                          {/* Modality Tag: camera used vs voice used vs text used */}
                          <span
                            className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded-full font-bold inline-flex items-center gap-1 ${
                              entry.modality === "camera used"
                                ? "bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/20"
                                : entry.modality === "voice used"
                                ? "bg-purple-500/15 text-purple-700 dark:text-purple-300 border border-purple-500/20"
                                : "bg-forest/15 text-forest border border-forest/20"
                            }`}
                          >
                            {entry.modality === "camera used" ? (
                              <>
                                <Camera className="h-2.5 w-2.5" />
                                <span>Camera Used</span>
                              </>
                            ) : entry.modality === "voice used" ? (
                              <>
                                <Mic className="h-2.5 w-2.5" />
                                <span>Voice Used</span>
                              </>
                            ) : (
                              <>
                                <FileText className="h-2.5 w-2.5" />
                                <span>Text Used</span>
                              </>
                            )}
                          </span>
                        </div>
                        <div className="text-xs text-foreground/55 mt-0.5">
                          Felt {entry.moodLabel} · {entry.sleepHours}h rest
                          {entry.modality === "camera used" && entry.camera_distress_score !== undefined && (
                            <span className="ml-1.5 text-amber-600 font-mono">
                              · OpenCV {Math.round(entry.camera_distress_score * 100)}% ({entry.primary_emotion || "NEUTRAL"})
                            </span>
                          )}
                          {entry.modality === "voice used" && entry.voice_stress_score !== undefined && (
                            <span className="ml-1.5 text-purple-600 font-mono">
                              · Acoustic {Math.round(entry.voice_stress_score * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <span className="text-xs text-clay font-medium opacity-80 group-hover:opacity-100">
                      View →
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Selected Entry Deep View */}
          <div className="md:col-span-6">
            {selectedEntry ? (
              <div className="rounded-3xl border border-foreground/10 bg-card p-6 md:p-8 space-y-6 shadow-[var(--shadow-soft)] sticky top-6">
                <div className="flex items-center justify-between border-b border-foreground/10 pb-4">
                  <div>
                    <span className="text-[10px] font-medium uppercase tracking-widest text-clay">
                      Rereading Reflection
                    </span>
                    <h3 className="font-display text-3xl">
                      {new Date(selectedEntry.date).toLocaleDateString("en-IN", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                      })}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDelete(selectedEntry.id)}
                    className="p-2 text-foreground/40 hover:text-clay transition-colors rounded-lg hover:bg-foreground/5"
                    title="Delete entry privately"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-2xl bg-foreground/5 p-4">
                    <span className="text-xs text-foreground/50 block mb-1">State of Mind</span>
                    <span className="font-display text-2xl text-foreground">
                      {selectedEntry.moodLabel}
                    </span>
                  </div>
                  <div className="rounded-2xl bg-foreground/5 p-4">
                    <span className="text-xs text-foreground/50 block mb-1">Rest</span>
                    <span className="font-display text-2xl text-foreground">
                      {selectedEntry.sleepHours} hrs ({selectedEntry.sleepQuality})
                    </span>
                  </div>
                </div>

                {/* Modality & Perception Signal Card */}
                <div className={`p-4 rounded-2xl border ${
                  selectedEntry.modality === "camera used"
                    ? "border-amber-500/30 bg-amber-500/5"
                    : selectedEntry.modality === "voice used"
                    ? "border-purple-500/30 bg-purple-500/5"
                    : "border-forest/25 bg-forest/5"
                } space-y-2`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {selectedEntry.modality === "camera used" ? (
                        <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-600">
                          <Camera className="h-4 w-4" />
                        </div>
                      ) : selectedEntry.modality === "voice used" ? (
                        <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-600">
                          <Mic className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="p-1.5 rounded-lg bg-forest/20 text-forest">
                          <FileText className="h-4 w-4" />
                        </div>
                      )}
                      <div>
                        <span className="text-xs font-semibold uppercase tracking-wider block font-mono">
                          {selectedEntry.modality === "camera used"
                            ? "Camera Used · OpenCV FER+ Averaging"
                            : selectedEntry.modality === "voice used"
                            ? "Voice Used · Acoustic Scoring"
                            : "Text Used · MuRIL Perception"}
                        </span>
                        <span className="text-[10px] text-foreground/50">
                          {selectedEntry.modality === "camera used"
                            ? "Assessed via OpenCV ONNX Net (:8400/api/v1/perception/camera-average)"
                            : selectedEntry.modality === "voice used"
                            ? "Assessed via Sohon's Voice Model (:8100/v1/signals/voice)"
                            : "Assessed via Sohon's MuRIL Text Model (:8100/v1/signals/text)"}
                        </span>
                      </div>
                    </div>

                    <span className={`text-[10px] uppercase font-mono px-2.5 py-1 rounded-full font-bold ${
                      selectedEntry.modality === "camera used"
                        ? "bg-amber-500/20 text-amber-700 dark:text-amber-300"
                        : selectedEntry.modality === "voice used"
                        ? "bg-purple-500/20 text-purple-700 dark:text-purple-300"
                        : "bg-forest/20 text-forest"
                    }`}>
                      {selectedEntry.modality === "camera used"
                        ? "Camera Used"
                        : selectedEntry.modality === "voice used"
                        ? "Voice Used"
                        : "Text Used"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-foreground/5 text-xs">
                    {selectedEntry.modality === "camera used" ? (
                      <>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Averaged Visual Distress</span>
                          <span className="font-mono font-bold text-amber-600 text-sm">
                            {Math.round((selectedEntry.camera_distress_score ?? 0.35) * 100)}%
                          </span>
                        </div>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Primary Facial Emotion</span>
                          <span className="font-medium text-foreground text-xs leading-snug capitalize">
                            {selectedEntry.primary_emotion || "Neutral"}
                          </span>
                        </div>
                        {selectedEntry.emotion_scores && (
                          <div className="col-span-2 p-2 rounded-xl bg-background/40 space-y-1.5 mt-1">
                            <span className="text-[9px] font-mono uppercase text-foreground/50 block">
                              OpenCV Session Emotion Breakdown
                            </span>
                            <div className="grid grid-cols-4 gap-1.5 text-[9px] font-mono">
                              {Object.entries(selectedEntry.emotion_scores).slice(0, 4).map(([emo, score]) => (
                                <div key={emo} className="bg-background/80 p-1 rounded border border-foreground/5 text-center">
                                  <span className="block text-foreground/50 capitalize truncate">{emo.toLowerCase()}</span>
                                  <span className="font-bold text-amber-600">{Math.round(score * 100)}%</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : selectedEntry.modality === "voice used" ? (
                      <>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Acoustic Stress</span>
                          <span className="font-mono font-bold text-clay text-sm">
                            {Math.round((selectedEntry.voice_stress_score ?? 0.28) * 100)}%
                          </span>
                        </div>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Voice Perception</span>
                          <span className="font-medium text-foreground text-xs leading-snug">
                            {selectedEntry.voice_label || "Acoustic Tone Logged"}
                          </span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Text Distress / Sentiment</span>
                          <span className="font-medium text-foreground text-xs leading-snug">
                            {selectedEntry.sentiment_label || "MuRIL Tone Analyzed"}
                          </span>
                        </div>
                        <div className="p-2 rounded-xl bg-background/60">
                          <span className="text-[10px] text-foreground/50 block">Threat Classification</span>
                          <span className={`font-mono font-bold text-xs ${
                            selectedEntry.threat_flag ? "text-red-500" : "text-green-600"
                          }`}>
                            {selectedEntry.threat_flag ? "Elevated Alert" : "Shielded (Safe)"}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-xs text-foreground/50 block mb-2">Feelings Noticed</span>
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.feelings.map((f) => (
                      <span
                        key={f}
                        className="rounded-full bg-sage/30 px-3 py-1 text-xs text-forest-deep"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedEntry.reflection && (
                  <div>
                    <span className="text-xs text-foreground/50 block mb-2">Personal Note</span>
                    <div className="rounded-2xl border border-foreground/10 bg-background/60 p-4 text-sm leading-relaxed italic text-foreground/80">
                      "{selectedEntry.reflection}"
                    </div>
                  </div>
                )}

                <div className="pt-2 text-[11px] text-foreground/40 text-center">
                  Stored securely on this browser only · No cloud telemetry
                </div>
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-foreground/15 p-12 text-center text-sm text-foreground/50">
                Select a day to reread its reflection
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
