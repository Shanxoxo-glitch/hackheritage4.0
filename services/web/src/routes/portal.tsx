import { createFileRoute, Link } from "@tanstack/react-router";
import { Reveal } from "@/components/landing/Reveal";
import heroHands from "@/assets/hero-hands.jpg";
import clayForm from "@/assets/clay-form.jpg";
import dawnField from "@/assets/dawn-field.jpg";
import {
  HeartHandshake,
  Stethoscope,
  BarChart3,
  ArrowRight,
  ShieldCheck,
  Layers,
  AlertTriangle,
} from "lucide-react";

export const Route = createFileRoute("/portal")({
  head: () => ({
    meta: [{ title: "Role Portal — Sahayak" }],
  }),
  component: RolePortalPage,
});

const ROLES = [
  {
    id: "victim",
    title: "Victim Sanctuary",
    subtitle: "Your private space",
    desc: "A warm, pseudonymous refuge for check-ins, crisis grounding, and confidential help requests. No accounts, no tracking. Just care.",
    image: heroHands,
    imageAlt: "Gentle hands around a warm cup — the victim sanctuary",
    links: [
      { label: "Daily Check-in", path: "/checkin" },
      { label: "Sanctuary Chat", path: "/chat" },
      { label: "Garden of Days", path: "/history" },
      { label: "Request Confidential Help", path: "/request" },
      { label: "India Helplines", path: "/help" },
    ],
    accent: "clay",
    accentClass: "text-clay border-clay",
    bgClass: "bg-card",
    badgeClass: "bg-clay/15 text-clay",
    Icon: HeartHandshake,
  },
  {
    id: "counsellor",
    title: "Counsellor Field Office",
    subtitle: "Clinical dashboard",
    desc: "A tactile, warm workspace for counsellors — paper-file case records, field clinical notes, explainable AI triage, and status ribbon management.",
    image: clayForm,
    imageAlt: "Warm clay textures — the counsellor field office",
    links: [
      { label: "Assigned Cases & Field Notes", path: "/counsellor" },
      { label: "CaseWriter Clinical Studio", path: "/casewriter" },
      { label: "Triage Alert Queue", path: "/counsellor/alerts" },
      { label: "AI Decision Trace Audit", path: "/counsellor/trace/thread-8492" },
    ],
    accent: "forest",
    accentClass: "text-forest border-forest",
    bgClass: "bg-card",
    badgeClass: "bg-forest/15 text-forest",
    Icon: Stethoscope,
  },
  {
    id: "admin",
    title: "Admin Observatory",
    subtitle: "Aggregated insights",
    desc: "A softly lit command view with animated community wellbeing charts, district triage distribution, and SLA response monitoring — strictly no PII.",
    image: dawnField,
    imageAlt: "Misty dawn field — the admin observatory",
    links: [
      { label: "Full Observatory Dashboard", path: "/admin" },
    ],
    accent: "sage-deep",
    accentClass: "text-sage-deep border-sage-deep",
    bgClass: "bg-card",
    badgeClass: "bg-sage/40 text-sage-deep",
    Icon: BarChart3,
  },
];

export default function RolePortalPage() {
  return (
    <div className="grain min-h-screen bg-background text-foreground">
      {/* Hero Header */}
      <header className="mx-auto max-w-7xl px-6 pt-12 pb-8 md:px-10">
        <div className="flex items-center justify-between mb-10">
          <Link
            to="/"
            className="font-display text-3xl text-foreground hover:text-clay transition-colors flex items-center gap-2"
          >
            Sahayak
            <span className="h-1.5 w-1.5 rounded-full bg-clay animate-breathe" />
          </Link>
          <div className="flex items-center gap-2 text-xs text-foreground/60 border border-foreground/15 rounded-full px-3 py-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-sage-deep" />
            <span>Hackathon Demo · All roles visible</span>
          </div>
        </div>

        <Reveal>
          <div className="max-w-3xl space-y-4">
            <span className="text-xs font-medium uppercase tracking-[0.28em] text-clay">
              Multi-Role Access Portal
            </span>
            <h1 className="text-5xl md:text-7xl font-display leading-[0.9]">
              Choose your
              <br />
              <em className="italic text-clay">perspective.</em>
            </h1>
            <p className="text-lg text-foreground/70 max-w-2xl leading-relaxed">
              Sahayak operates across three distinct roles — each with its own signature look, purpose, and
              data boundary. Explore them below to see how the platform holds care at every layer.
            </p>
          </div>
        </Reveal>
      </header>

      {/* Role Cards Grid */}
      <main className="mx-auto max-w-7xl px-6 pb-20 md:px-10">
        <div className="grid md:grid-cols-3 gap-6 mt-4">
          {ROLES.map((role, i) => (
            <Reveal key={role.id} delay={i * 150}>
              <div className="group flex flex-col rounded-[2.5rem] border border-foreground/10 bg-card overflow-hidden shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-lift)] hover:border-foreground/20 transition-all duration-500">
                {/* Image Header */}
                <div className="relative h-52 overflow-hidden">
                  <img
                    src={role.image}
                    alt={role.imageAlt}
                    className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-card via-card/40 to-transparent" />

                  {/* Role Badge */}
                  <div className="absolute top-4 left-4">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-wider ${role.badgeClass}`}
                    >
                      <role.Icon className="h-3.5 w-3.5" />
                      {role.subtitle}
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="flex flex-col flex-1 p-6 space-y-4">
                  <div>
                    <h2 className="font-display text-2xl text-foreground">{role.title}</h2>
                    <p className="text-xs text-foreground/65 mt-2 leading-relaxed">{role.desc}</p>
                  </div>

                  {/* Quick Link List */}
                  <ul className="space-y-1.5 flex-1">
                    {role.links.map((lnk) => (
                      <li key={lnk.path}>
                        <Link
                          to={lnk.path}
                          className={`flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium text-foreground/75 hover:bg-foreground/5 hover:${role.accentClass.split(" ")[0]} transition-colors group/link`}
                        >
                          <span>{lnk.label}</span>
                          <ArrowRight className="h-3 w-3 opacity-0 -translate-x-1 group-hover/link:opacity-100 group-hover/link:translate-x-0 transition-all" />
                        </Link>
                      </li>
                    ))}
                  </ul>

                  {/* Primary CTA */}
                  <Link
                    to={role.links[0].path}
                    className="mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-forest px-6 py-3 text-sm font-medium text-forest-foreground shadow-sm hover:bg-clay transition-all duration-300"
                  >
                    <span>Enter {role.title.split(" ")[0]} View</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Demo Note */}
        <Reveal delay={400}>
          <div className="mt-10 rounded-2xl border border-foreground/10 bg-sage/15 p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Layers className="h-5 w-5 text-sage-deep flex-shrink-0 mt-0.5 sm:mt-0" />
            <div className="text-xs text-foreground/75 leading-relaxed flex-1">
              <strong className="text-foreground">Hackathon Demo Notice:</strong> Role switching is UI-only.
              In production, each role has isolated authentication scopes (victim pseudonymous session,
              counsellor OTP-authenticated named session, admin ops scope). The backend orchestrator at{" "}
              <code className="font-mono bg-foreground/5 px-1 py-0.5 rounded text-[10px]">:8500</code> enforces
              row-level security — counsellors only see assigned cases, and no victim data crosses role
              boundaries without explicit escalation consent.
            </div>
          </div>
        </Reveal>
      </main>
    </div>
  );
}
