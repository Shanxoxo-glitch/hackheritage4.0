import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Reveal } from "@/components/landing/Reveal";
import heroHands from "@/assets/hero-hands.jpg";
import clayForm from "@/assets/clay-form.jpg";
import listening from "@/assets/listening.jpg";
import dawnField from "@/assets/dawn-field.jpg";
import { Sparkles, HeartHandshake, ShieldCheck, ArrowRight, MessageCircle } from "lucide-react";
import { BottomNavbar } from "@/components/common/BottomNavbar";
import { AuthModal } from "@/components/auth/AuthModal";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Sahayak — Anonymous support for heavy moments" },
      {
        name: "description",
        content:
          "Sahayak is a private, anonymous space to steady yourself, unburden and reach a counsellor when you're ready. No account, no tracking.",
      },
      { property: "og:title", content: "Sahayak — Anonymous support for heavy moments" },
      {
        property: "og:description",
        content:
          "A quiet, anonymous sanctuary for the moments that feel too heavy to carry alone. Grounding, unburdening and human support.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Landing,
});

const journey = [
  {
    n: "01",
    title: "Grounding",
    body: "Simple sensory exercises and breathing rhythms that bring you back to the present moment when everything feels too loud.",
    tone: "text-sage-deep",
    link: "/checkin",
    action: "Begin check-in",
  },
  {
    n: "02",
    title: "Unburdening",
    body: "Say the thing you cannot say out loud. End-to-end encrypted, unrecorded, and accompanied by a steady, gentle presence.",
    tone: "text-clay",
    link: "/chat",
    action: "Enter quiet chat",
  },
  {
    n: "03",
    title: "Connecting",
    body: "Gentle pathways to a trained counsellor or local help — only if and when you want them, sealed with your secret codeword.",
    tone: "text-forest",
    link: "/request",
    action: "Request help",
  },
];

function CrisisPill() {
  return (
    <div className="fixed inset-x-0 top-4 z-40 flex justify-center px-4 pointer-events-none">
      <div className="flex items-center gap-3 pointer-events-auto">
        <a
          href="tel:14416"
          className="flex items-center gap-3 rounded-full bg-forest/95 px-4 py-2 text-forest-foreground shadow-[var(--shadow-lift)] backdrop-blur-sm transition-colors hover:bg-forest-deep"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-breathe absolute inline-flex h-full w-full rounded-full bg-clay" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-clay" />
          </span>
          <span className="text-[10px] font-medium uppercase tracking-[0.2em]">
            Immediate Crisis
          </span>
          <span className="border-l border-forest-foreground/25 pl-3 text-xs font-medium">
            14416 (Tele-MANAS)
          </span>
        </a>

        <Link
          to="/help"
          className="hidden sm:inline-flex rounded-full bg-card/90 px-3.5 py-2 text-xs font-medium text-foreground/80 shadow-[var(--shadow-lift)] backdrop-blur-sm transition-colors hover:bg-card hover:text-clay border border-foreground/10"
        >
          All Helplines
        </Link>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="mx-auto grid max-w-7xl items-center gap-14 px-6 pb-20 pt-0 md:px-10 lg:grid-cols-2 lg:gap-20 lg:pt-[0.1rem]">
      <div className="order-2 flex flex-col gap-8 lg:order-1">
        <Reveal>
          <div className="inline-flex items-center gap-2 rounded-full border border-clay/30 bg-clay/10 px-3.5 py-1 text-xs font-medium uppercase tracking-[0.24em] text-clay">
            <Sparkles className="h-3 w-3" />
            <span>Anonymous Care Sanctuary</span>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <h1 className="text-6xl leading-[0.88] tracking-tight md:text-7xl lg:text-8xl">
            Find your
            <br />
            <em className="italic text-clay">inner calm.</em>
          </h1>
        </Reveal>
        <Reveal delay={240}>
          <p className="max-w-lg text-xl leading-relaxed text-foreground/75 md:text-2xl">
            A quiet place for the moments that feel too heavy to carry alone.
            Anonymous, encrypted, and built with human care.
          </p>
        </Reveal>
        <Reveal delay={360}>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              to="/checkin"
              className="rounded-full bg-forest px-8 py-4 text-base text-forest-foreground shadow-[var(--shadow-soft)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-clay"
            >
              Start daily check-in
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 rounded-full border border-foreground/20 px-6 py-4 text-base text-foreground transition-colors hover:border-clay hover:text-clay"
            >
              <MessageCircle className="h-4 w-4 text-clay" />
              <span>Quiet chat</span>
            </Link>
          </div>
          <div className="flex items-center gap-6 pt-2 text-xs text-foreground/60">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-sage-deep" /> Zero account required
            </span>
            <span>·</span>
            <span>No data harvesting</span>
            <span>·</span>
            <Link to="/help" className="underline hover:text-clay">
              India 24/7 Helplines
            </Link>
          </div>
        </Reveal>
      </div>

      <div className="order-1 lg:order-2">
        <div className="overflow-hidden rounded-[60px] border-8 border-clay shadow-[var(--shadow-soft)] lg:rounded-b-[60px] lg:rounded-t-[280px]">
          <img
            src={heroHands}
            alt="Hands cradling a warm clay cup in soft morning light"
            width={912}
            height={1200}
            className="h-full min-h-[420px] w-full object-cover lg:min-h-[600px]"
          />
        </div>
      </div>
    </section>
  );
}

function Journey() {
  return (
    <section id="journey" className="mx-auto max-w-7xl px-6 py-16 md:px-10 relative">
      {/* Leaf-vine PNG decorating the left side above the three cards — covers over half screen */}
      <div className="vine-decoration absolute -top-72 pointer-events-none select-none opacity-90 z-0" aria-hidden="true">
        <img
          src="/leaf-vine-isolate-on-transparent-background-file-png.webp"
          alt=""
          className="w-full h-auto object-contain"
        />
      </div>

      <div className="relative z-10 grid gap-12 border-t border-foreground/10 pt-16 md:grid-cols-3">
        {journey.map((step, i) => (
          <Reveal key={step.n} delay={i * 140}>
            <div className={`group flex flex-col gap-4 rounded-3xl p-6 cursor-pointer ${
              step.n === "02" ? "border border-clay/35" : "border border-foreground/5"
            } ${
              step.n === "01" || step.n === "03" ? "bg-clay" : "bg-white"
            }`}>
              <span className={`font-display text-5xl ${step.n === "01" || step.n === "03" ? "text-white" : step.tone}`}>{step.n}</span>
              <h3 className={`text-2xl font-display ${step.n === "01" || step.n === "03" ? "text-white" : "text-foreground"}`}>{step.title}</h3>
              <p className={`leading-relaxed text-sm flex-1 ${step.n === "01" || step.n === "03" ? "text-white" : "text-foreground/70"}`}>{step.body}</p>
              <Link
                to={step.link}
                className={`mt-2 inline-flex items-center gap-1.5 text-xs font-medium uppercase tracking-[0.16em] ${step.n === "01" || step.n === "03" ? "text-white" : "text-clay"}`}
              >
                <span>{step.action}</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function HowItHelps() {
  return (
    <section id="help" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <div className="grid items-center gap-14 lg:grid-cols-2">
        <Reveal>
          <div className="overflow-hidden rounded-[48px] shadow-[0_30px_75px_-15px_rgba(25,45,35,0.45),0_15px_35px_-10px_rgba(0,0,0,0.25)] border border-foreground/10">
            <img
              src={listening}
              alt="Two people sitting together in warm afternoon light, one listening closely"
              width={1008}
              height={752}
              loading="lazy"
              className="h-full w-full object-cover"
            />
          </div>
        </Reveal>
        <Reveal delay={140}>
          <div className="flex flex-col gap-8">
            <h2 className="text-4xl italic md:text-5xl font-display"><em className="text-clay">Held,</em> not handled.</h2>
            <div className="flex flex-col divide-y divide-foreground/10">
              {[
                {
                  t: "Talk anonymously, right now",
                  d: "No name, no number, no account. Just an unburdening sanctuary whenever the night gets heavy.",
                  link: "/chat",
                },
                {
                  t: "A gentle daily check-in",
                  d: "One question per page that takes 60 seconds and quietly visualizes your week as an organic garden.",
                  link: "/checkin",
                },
                {
                  t: "A counsellor when you want one",
                  d: "Trained professionals you can reach with a secret codeword — never pushed, never assigned without your yes.",
                  link: "/request",
                },
              ].map((item) => (
                <div key={item.t} className="group py-6">
                  <Link to={item.link}>
                    <h3 className="text-xl transition-colors duration-300 group-hover:text-clay font-display">
                      {item.t}
                    </h3>
                  </Link>
                  <p className="mt-2 leading-relaxed text-foreground/65 text-sm">{item.d}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function Privacy() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <Reveal>
        <div className="flex flex-col items-center gap-14 rounded-[60px] bg-sage/25 p-10 md:flex-row md:p-20">
          <div className="flex-1">
            <h2 className="mb-6 text-4xl italic md:text-5xl font-display">
              Your privacy is
              <br />
              our foundation.
            </h2>
            <p className="max-w-xl text-base md:text-lg leading-relaxed text-foreground/80">
              Sahayak is built on radical anonymity. Every interaction stays in your browser
              session. Nothing is sold, nothing is linked to your device, and you never need an
              account to be heard.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                to="/history"
                className="rounded-full bg-forest px-6 py-3 text-sm text-forest-foreground transition-colors hover:bg-clay"
              >
                View Your Check-in Garden
              </Link>
              <Link
                to="/help"
                className="rounded-full border border-forest/30 px-6 py-3 text-sm text-forest transition-colors hover:bg-card"
              >
                Emergency Helplines
              </Link>
            </div>
          </div>
          <div className="w-full md:w-1/3">
            <div className="overflow-hidden aspect-square w-full rounded-full border-8 border-forest shadow-[var(--shadow-soft)]">
              <img
                src={clayForm}
                alt="A soft clay sculpture in warm light"
                width={816}
                height={816}
                loading="lazy"
                className="h-full w-full object-cover"
              />
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

function Closing() {
  return (
    <section className="relative mt-8 overflow-hidden">
      <img
        src={dawnField}
        alt="Mist settling over a quiet field at dawn"
        width={1600}
        height={912}
        loading="lazy"
        className="h-[55vh] min-h-[400px] w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent" />
      <div className="absolute inset-0 flex items-end justify-center pb-16">
        <Reveal className="px-6 text-center">
          <h2 className="mx-auto max-w-2xl text-4xl leading-tight md:text-6xl font-display">
            Whatever tonight holds,
            <br />
            <em className="italic text-clay">you don't hold it alone.</em>
          </h2>
          <div className="mt-8 flex justify-center gap-4">
            <Link
              to="/checkin"
              className="rounded-full bg-forest px-9 py-4 text-base text-forest-foreground shadow-[var(--shadow-soft)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-clay"
            >
              Start check-in
            </Link>
            <Link
              to="/request"
              className="rounded-full bg-card/80 border border-foreground/20 px-7 py-4 text-base text-foreground transition-all duration-300 hover:border-clay hover:text-clay backdrop-blur-sm"
            >
              Request confidential support
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="relative overflow-hidden bg-forest text-forest-foreground">
      <div className="relative z-10 mx-auto grid max-w-7xl gap-10 px-6 py-16 md:grid-cols-[repeat(4,minmax(0,1fr))] md:pr-[28%] md:px-10">
        <div className="md:col-span-1">
          <p className="font-display text-3xl">Sahayak</p>
          <p className="mt-3 text-xs leading-relaxed text-forest-foreground/65">
            Anonymous emotional sanctuary & multi-role crisis support. Built with care for
            communities across India. Not an emergency dispatch substitute.
          </p>
        </div>
        <div className="text-xs leading-loose text-forest-foreground/75">
          <p className="mb-2 text-[10px] uppercase tracking-[0.24em] text-forest-foreground/50 font-medium">
            Immediate Indian Helplines
          </p>
          <p>Tele-MANAS: <a href="tel:14416" className="underline hover:text-clay-soft">14416</a></p>
          <p>Kiran: <a href="tel:18005990019" className="underline hover:text-clay-soft">1800-599-0019</a></p>
          <p>Vandrevala: <a href="tel:9999666555" className="underline hover:text-clay-soft">9999 666 555</a></p>
          <p>National Emergency: <a href="tel:112" className="underline hover:text-clay-soft">112</a></p>
        </div>
        <div className="text-xs leading-loose text-forest-foreground/75">
          <p className="mb-2 text-[10px] uppercase tracking-[0.24em] text-forest-foreground/50 font-medium">
            Victim Sanctuary
          </p>
          <p><Link to="/checkin" className="hover:underline">Daily Check-in</Link></p>
          <p><Link to="/chat" className="hover:underline">Crisis Chat (with Orb)</Link></p>
          <p><Link to="/history" className="hover:underline">Garden of Days</Link></p>
          <p><Link to="/request" className="hover:underline">Confidential Request</Link></p>
          <p><Link to="/status" className="hover:underline">Check Codeword Status</Link></p>
        </div>
        <div className="text-xs leading-loose text-forest-foreground/75">
          <p className="mb-2 text-[10px] uppercase tracking-[0.24em] text-forest-foreground/50 font-medium">
            Professional & Ops
          </p>
          <p><Link to="/counsellor" className="hover:underline">Counsellor Field Office</Link></p>
          <p><Link to="/counsellor/alerts" className="hover:underline">Triage Alert Queue</Link></p>
          <p><Link to="/admin" className="hover:underline">Admin Observatory</Link></p>
          <p><Link to="/portal" className="hover:underline">Demo Role Hub</Link></p>
          <p><Link to="/help" className="hover:underline">All Helplines Directory</Link></p>
        </div>
      </div>
      <div className="pointer-events-none absolute inset-x-4 top-0 bottom-4 hidden md:block" aria-hidden="true">
        <img
          src="/pngtree-3d-decorative-pillar-around-flower-design-png-image_11379314.png"
          alt=""
          className="ml-auto h-full w-[28%] translate-x-16 object-contain object-bottom"
        />
      </div>
    </footer>
  );
}

function Landing() {
  const [authOpen, setAuthOpen] = useState(false);

  return (
    <main className="grain min-h-screen bg-background">
      <CrisisPill />
      <Hero />
      <Journey />
      <HowItHelps />
      <Privacy />
      <Closing />
      <Footer />

      <BottomNavbar onOpenAuth={() => setAuthOpen(true)} />

      {/* Auth Modal — login / signup with role selection and Spline gradient */}
      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </main>
  );
}
