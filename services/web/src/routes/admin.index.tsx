import { createFileRoute, Link } from "@tanstack/react-router";
import { getCheckIns, getAlerts, getCases } from "@/lib/store";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { ArrowLeft, BarChart3, TrendingUp, Globe, Users, Clock } from "lucide-react";

export const Route = createFileRoute("/admin/")({
  head: () => ({
    meta: [{ title: "Admin Observatory — Sahayak" }],
  }),
  component: AdminObservatoryPage,
});

// Pre-seeded aggregated observatory data — no PII
const MOOD_TREND_DATA = [
  { date: "Sep 1", avg_wellbeing: 0.52, check_ins: 14 },
  { date: "Sep 2", avg_wellbeing: 0.48, check_ins: 11 },
  { date: "Sep 3", avg_wellbeing: 0.55, check_ins: 17 },
  { date: "Sep 4", avg_wellbeing: 0.61, check_ins: 22 },
  { date: "Sep 5", avg_wellbeing: 0.58, check_ins: 19 },
  { date: "Sep 6", avg_wellbeing: 0.64, check_ins: 25 },
  { date: "Sep 7", avg_wellbeing: 0.67, check_ins: 28 },
  { date: "Sep 8", avg_wellbeing: 0.63, check_ins: 31 },
  { date: "Sep 9", avg_wellbeing: 0.7, check_ins: 29 },
];

const DISTRICT_DATA = [
  { name: "Bengaluru Urban", open: 12, resolved: 34 },
  { name: "Pune", open: 8, resolved: 21 },
  { name: "New Delhi", open: 18, resolved: 42 },
  { name: "Chennai", open: 6, resolved: 15 },
  { name: "Kolkata", open: 9, resolved: 27 },
];

const RESPONSE_TIME_DATA = [
  { window: "< 2h", count: 38 },
  { window: "2–6h", count: 22 },
  { window: "6–12h", count: 9 },
  { window: "12–24h", count: 5 },
  { window: "> 24h", count: 2 },
];

const STATUS_DISTRIBUTION = [
  { name: "Active Support", value: 29, color: "var(--color-forest)" },
  { name: "Contacted", value: 21, color: "var(--color-clay)" },
  { name: "Resolved", value: 139, color: "var(--color-sage)" },
  { name: "New Intake", value: 8, color: "var(--color-clay-soft)" },
];

function StatTile({
  label,
  value,
  sub,
  color = "text-foreground",
}: {
  label: string;
  value: string;
  sub: string;
  color?: string;
}) {
  return (
    <div className="rounded-2xl border border-foreground/10 bg-card p-5 space-y-1 hover:border-clay/30 transition-colors group">
      <span className="text-xs text-foreground/50 uppercase tracking-wider font-medium">{label}</span>
      <div className={`font-display text-3xl font-bold transition-colors group-hover:text-clay ${color}`}>
        {value}
      </div>
      <div className="text-[11px] text-foreground/55">{sub}</div>
    </div>
  );
}

export default function AdminObservatoryPage() {
  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-7xl space-y-10">
        {/* Observatory Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-foreground/10 pb-6">
          <div className="space-y-2">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Sanctuary</span>
            </Link>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-sage-deep">
              <Globe className="h-4 w-4" />
              <span>Aggregated · Privacy-Preserving · No PII</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-display">
              Sahayak Observatory
            </h1>
            <p className="text-sm text-foreground/65">
              System-wide care metrics, district triage distribution, and community wellbeing trends.
            </p>
          </div>
          <div className="text-xs text-foreground/40 font-mono self-start sm:self-auto">
            Last updated: {new Date().toLocaleTimeString("en-IN")}
          </div>
        </div>

        {/* Glowing Aggregate Stat Tiles */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatTile
            label="Total Check-ins"
            value="1,847"
            sub="Across all districts · Sept 2026"
            color="text-forest"
          />
          <StatTile
            label="Active Cases"
            value="58"
            sub="In triage or active support"
            color="text-clay"
          />
          <StatTile
            label="Cases Resolved"
            value="139"
            sub="Safely closed with care"
            color="text-sage-deep"
          />
          <StatTile
            label="Avg Response"
            value="3.2h"
            sub="From intake to first contact"
            color="text-foreground"
          />
        </div>

        {/* Main Charts Row */}
        <div className="grid lg:grid-cols-12 gap-6">
          {/* Area Chart: Community Wellbeing Trend */}
          <div className="lg:col-span-7 rounded-3xl border border-foreground/10 bg-card p-6 space-y-4 shadow-[var(--shadow-soft)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-sage-deep" />
                <span className="text-sm font-semibold text-foreground">Community Wellbeing Trend</span>
              </div>
              <span className="text-xs text-foreground/45">14-day rolling avg · Anonymized</span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={MOOD_TREND_DATA} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id="wellbeingGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-sage)" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="var(--color-sage)" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  stroke="currentColor"
                  className="text-[10px] text-foreground/40 font-mono"
                  tickLine={false}
                  axisLine={{ stroke: "rgba(100,100,100,0.1)" }}
                />
                <YAxis
                  domain={[0.3, 1]}
                  stroke="currentColor"
                  className="text-[10px] font-mono"
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid rgba(100,100,100,0.15)",
                    borderRadius: "12px",
                    fontSize: "11px",
                    color: "var(--color-foreground)",
                  }}
                  formatter={(v: number) => [`${(v * 100).toFixed(0)}%`, "Wellbeing Index"]}
                />
                <Area
                  type="monotone"
                  dataKey="avg_wellbeing"
                  stroke="var(--color-sage-deep)"
                  strokeWidth={2.5}
                  fill="url(#wellbeingGradient)"
                  dot={{ r: 3, fill: "var(--color-sage-deep)" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Pie: Status Distribution */}
          <div className="lg:col-span-5 rounded-3xl border border-foreground/10 bg-card p-6 space-y-4 shadow-[var(--shadow-soft)]">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-clay" />
              <span className="text-sm font-semibold text-foreground">Case Status Distribution</span>
            </div>
            <div className="flex items-center gap-6">
              <ResponsiveContainer width={130} height={130}>
                <PieChart>
                  <Pie
                    data={STATUS_DISTRIBUTION}
                    cx={60}
                    cy={60}
                    innerRadius={36}
                    outerRadius={58}
                    dataKey="value"
                    strokeWidth={2}
                    stroke="var(--color-background)"
                  >
                    {STATUS_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {STATUS_DISTRIBUTION.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                        style={{ background: item.color }}
                      />
                      <span className="text-foreground/75">{item.name}</span>
                    </div>
                    <span className="font-mono font-semibold text-foreground">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Charts Row */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Bar Chart: District Breakdown */}
          <div className="rounded-3xl border border-foreground/10 bg-card p-6 space-y-4 shadow-[var(--shadow-soft)]">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-forest" />
              <span className="text-sm font-semibold text-foreground">District Caseload Breakdown</span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={DISTRICT_DATA}
                margin={{ top: 4, right: 8, left: -24, bottom: 0 }}
                barGap={2}
              >
                <XAxis
                  dataKey="name"
                  stroke="currentColor"
                  className="text-[9px] font-mono"
                  tickLine={false}
                  axisLine={false}
                  interval={0}
                  tick={{ fontSize: 9 }}
                />
                <YAxis
                  stroke="currentColor"
                  className="text-[10px] font-mono"
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid rgba(100,100,100,0.15)",
                    borderRadius: "12px",
                    fontSize: "11px",
                  }}
                />
                <Bar dataKey="resolved" name="Resolved" fill="var(--color-sage)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="open" name="Open" fill="var(--color-clay)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-4 text-[11px] text-foreground/60">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm" style={{ background: "var(--color-sage)" }} />
                Resolved
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm" style={{ background: "var(--color-clay)" }} />
                Open
              </span>
            </div>
          </div>

          {/* Bar Chart: Response Times */}
          <div className="rounded-3xl border border-foreground/10 bg-card p-6 space-y-4 shadow-[var(--shadow-soft)]">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-clay" />
              <span className="text-sm font-semibold text-foreground">
                Response Time Distribution (SLA Monitoring)
              </span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={RESPONSE_TIME_DATA}
                margin={{ top: 4, right: 8, left: -24, bottom: 0 }}
              >
                <XAxis
                  dataKey="window"
                  stroke="currentColor"
                  className="text-[10px] font-mono"
                  tickLine={false}
                  axisLine={{ stroke: "rgba(100,100,100,0.1)" }}
                />
                <YAxis
                  stroke="currentColor"
                  className="text-[10px] font-mono"
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid rgba(100,100,100,0.15)",
                    borderRadius: "12px",
                    fontSize: "11px",
                  }}
                  formatter={(v: number) => [v, "Cases"]}
                />
                <Bar dataKey="count" name="Cases" radius={[6, 6, 0, 0]}>
                  {RESPONSE_TIME_DATA.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        index === 0
                          ? "var(--color-forest)"
                          : index === 1
                          ? "var(--color-sage-deep)"
                          : index === 2
                          ? "var(--color-clay-soft)"
                          : "var(--color-clay)"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-foreground/50">
              80% of cases receive first human contact within 6 hours.
            </p>
          </div>
        </div>

        {/* Footer Note */}
        <div className="text-center text-xs text-foreground/40 pt-4">
          All observatory metrics are strictly aggregated. Zero individual records are visible in
          this view. No victim PII is ever accessible without direct case assignment.
        </div>
      </div>
    </div>
  );
}
