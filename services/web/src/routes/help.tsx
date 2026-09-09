import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, PhoneCall, ShieldCheck, Heart, Sparkles, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/help")({
  head: () => ({
    meta: [{ title: "India Crisis Helplines — Sahayak" }],
  }),
  component: HelplinesPage,
});

const HELPLINES = [
  {
    name: "Tele-MANAS",
    number: "14416",
    tel: "14416",
    org: "Ministry of Health & Family Welfare, Govt. of India",
    desc: "Toll-free 24/7 national mental health helpline providing comprehensive psychological support across 20+ Indian languages.",
    badge: "24/7 · Toll Free · Govt of India",
    primary: true,
  },
  {
    name: "KIRAN Helpline",
    number: "1800-599-0019",
    tel: "18005990019",
    org: "Dept. of Empowerment of Persons with Disabilities",
    desc: "24/7 mental health rehabilitation helpline offering clinical psychological first aid and distress management.",
    badge: "24/7 · Toll Free · 13 Languages",
    primary: true,
  },
  {
    name: "Vandrevala Foundation",
    number: "+91 9999 666 555",
    tel: "9999666555",
    org: "Cyrus & Priya Vandrevala Foundation",
    desc: "Round-the-clock free crisis intervention and psychological counselling by trained professionals.",
    badge: "24/7 · Crisis Intervention",
    primary: false,
  },
  {
    name: "AASRA",
    number: "+91 98204 66726",
    tel: "9820466726",
    org: "AASRA Suicide Prevention Foundation",
    desc: "Confidential suicide prevention and emotional support helpline operating 24 hours daily.",
    badge: "24/7 · Suicide Prevention",
    primary: false,
  },
  {
    name: "Women in Distress Helpline",
    number: "181",
    tel: "181",
    org: "National Commission for Women",
    desc: "24-hour toll-free emergency response helpline for women in distress, domestic violence, or abuse.",
    badge: "24/7 · Toll Free · Domestic Safety",
    primary: false,
  },
  {
    name: "Childline India",
    number: "1098",
    tel: "1098",
    org: "Ministry of Women & Child Development",
    desc: "24/7 free emergency helpline for children in need of aid and protection.",
    badge: "24/7 · For Youth & Children",
    primary: false,
  },
  {
    name: "National Emergency Number",
    number: "112",
    tel: "112",
    org: "Unified Emergency Response System",
    desc: "Single emergency number for police, ambulance, and fire services across all states of India.",
    badge: "Immediate Physical Emergency",
    primary: false,
  },
];

export default function HelplinesPage() {
  return (
    <div className="grain min-h-screen bg-background text-foreground p-6 md:p-12">
      <div className="mx-auto max-w-4xl space-y-10">
        {/* Header */}
        <div className="space-y-3 border-b border-foreground/10 pb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-foreground/60 hover:text-clay transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Sanctuary</span>
          </Link>
          <div className="flex items-center gap-2 text-clay text-xs font-semibold uppercase tracking-widest">
            <ShieldCheck className="h-4 w-4" />
            <span>Verified 24/7 Directory</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-display">Immediate Helplines in India</h1>
          <p className="text-sm text-foreground/70 max-w-2xl leading-relaxed">
            If you are in immediate physical danger, feeling overwhelmed, or need a voice right now,
            these helplines are completely free, confidential, and available at this moment.
          </p>
        </div>

        {/* Priority Emergency Callout */}
        <div className="rounded-3xl border-2 border-clay bg-card p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-[var(--shadow-lift)]">
          <div className="space-y-2">
            <span className="rounded-full bg-clay/20 px-3 py-1 text-xs font-semibold text-clay uppercase tracking-wider inline-block">
              Primary Mental Health Helpline
            </span>
            <h2 className="font-display text-3xl">Tele-MANAS: Call 14416</h2>
            <p className="text-xs text-foreground/70 max-w-md">
              Govt. of India 24/7 toll-free psychiatric support in English, Hindi, Kannada, Tamil,
              Telugu, Bengali, Marathi, and 14 other languages.
            </p>
          </div>
          <a
            href="tel:14416"
            className="rounded-full bg-clay px-8 py-4 text-base font-semibold text-white shadow-[var(--shadow-lift)] hover:bg-forest transition-colors flex items-center gap-2.5 whitespace-nowrap self-stretch md:self-auto justify-center"
          >
            <PhoneCall className="h-5 w-5" />
            <span>Call 14416 Now</span>
          </a>
        </div>

        {/* Complete List of Helplines */}
        <div className="grid md:grid-cols-2 gap-4">
          {HELPLINES.map((h) => (
            <div
              key={h.name}
              className="rounded-2xl border border-foreground/10 bg-card p-5 space-y-3 hover:border-clay/40 transition-all flex flex-col justify-between"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-display text-xl text-foreground">{h.name}</h3>
                  <span className="rounded-full bg-foreground/5 px-2.5 py-0.5 text-[10px] font-medium text-foreground/60 whitespace-nowrap">
                    {h.badge}
                  </span>
                </div>
                <div className="text-[11px] text-clay font-medium">{h.org}</div>
                <p className="text-xs text-foreground/70 leading-relaxed pt-1">{h.desc}</p>
              </div>

              <div className="pt-3 border-t border-foreground/10 flex items-center justify-between">
                <span className="font-mono text-sm font-semibold text-foreground">{h.number}</span>
                <a
                  href={`tel:${h.tel}`}
                  className="inline-flex items-center gap-1.5 rounded-full bg-forest px-4 py-1.5 text-xs font-medium text-forest-foreground hover:bg-clay transition-colors"
                >
                  <PhoneCall className="h-3 w-3" />
                  <span>Call</span>
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Safety Note */}
        <div className="rounded-2xl border border-foreground/10 bg-sage/20 p-6 text-xs text-foreground/80 leading-relaxed space-y-2">
          <div className="font-semibold text-forest-deep flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>If someone is looking over your shoulder</span>
          </div>
          <p>
            Remember that you can press the <kbd className="font-mono bg-white/60 px-1.5 py-0.5 rounded text-[11px]">Esc</kbd> key
            or tap <strong>Quick Exit</strong> in the top-right corner to immediately close this
            page and clear all session evidence.
          </p>
        </div>
      </div>
    </div>
  );
}
