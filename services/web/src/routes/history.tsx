import { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { getCheckIns, deleteCheckIn, CheckInEntry } from "@/lib/store";
import { ArrowLeft, Trash2, Calendar, Sparkles, Moon, Sun, Flower2, Plus } from "lucide-react";

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
    const list = getCheckIns();
    setEntries(list);
    if (list.length > 0) {
      setSelectedEntry(list[0]);
    }
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
                        <div className="text-sm font-medium text-foreground">
                          {new Date(entry.date).toLocaleDateString("en-IN", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </div>
                        <div className="text-xs text-foreground/55">
                          Felt {entry.moodLabel} · {entry.sleepHours}h rest
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
