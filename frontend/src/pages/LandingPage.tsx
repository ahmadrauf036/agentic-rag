import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  FileText,
  Library,
  Lock,
  Mic,
  Zap,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/cn";

const btnBase =
  "inline-flex h-11 items-center justify-center gap-2 rounded-lg px-5 text-sm font-medium transition-all duration-150";
const btnPrimary = `${btnBase} bg-accent text-accent-fg shadow-glow hover:shadow-glow-lg hover:brightness-110`;
const btnSecondary = `${btnBase} border border-border bg-surface-2 text-fg hover:border-accent/60`;

const FEATURES = [
  {
    icon: Library,
    title: "A shared document library",
    text: "Pick one or more documents from the library your admins maintain, optionally narrow to a single page, then ask away.",
  },
  {
    icon: BookOpen,
    title: "Answers with sources",
    text: "See the file, page and passage behind an answer, so you can check it instead of taking it on trust.",
  },
  {
    icon: Zap,
    title: "Streams as it thinks",
    text: "Watch the answer arrive live, see which tools it used, and stop it any time.",
  },
  {
    icon: Mic,
    title: "Talk or listen",
    text: "Dictate your question with your voice, and have any answer read aloud to you.",
  },
  {
    icon: Lock,
    title: "Private chats",
    text: "Every chat belongs to your account. Your history stays yours and is there when you come back.",
  },
  {
    icon: FileText,
    title: "Locked to your documents",
    text: "Each chat is tied to the documents you chose, so answers stay grounded in them.",
  },
];

const STEPS = [
  { n: "1", title: "Choose documents", text: "Select from the shared library." },
  { n: "2", title: "Ask a question", text: "Type it, or say it." },
  { n: "3", title: "Check the sources", text: "Open the passages behind the answer." },
];

export default function LandingPage() {
  const { session, loading } = useAuth();
  const signedIn = !loading && !!session;

  return (
    <div className="relative min-h-full overflow-x-hidden bg-bg text-fg">
      {/* Ambient glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-[32rem]"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 0%, rgb(99 168 248 / 0.18), transparent 70%)",
        }}
      />

      {/* Nav */}
      <header className="relative z-10 mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 text-base font-semibold tracking-tight">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-accent-fg shadow-glow">
            <FileText size={15} />
          </span>
          RAG Chat
        </Link>
        <nav className="flex items-center gap-2" aria-label="Account">
          {signedIn ? (
            <Link to="/chat" className={cn(btnPrimary, "h-9 px-4")}>
              Open app
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-lg px-3 py-2 text-sm text-fg-muted transition-colors hover:text-fg"
              >
                Sign in
              </Link>
              <Link to="/login" state={{ mode: "signup" }} className={cn(btnPrimary, "h-9 px-4")}>
                Get started
              </Link>
            </>
          )}
        </nav>
      </header>

      <main className="relative z-10">
        {/* Hero */}
        <section className="mx-auto max-w-4xl px-4 pb-16 pt-14 text-center sm:pt-20">
          <p className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-fg-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent shadow-glow" />
            Chat with your documents
          </p>
          <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-6xl">
            Ask your documents.
            <br />
            <span className="text-accent">Get answers you can verify.</span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-pretty text-base text-fg-muted sm:text-lg">
            Pick documents, ask in plain language, and see exactly which pages each answer came
            from.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to={signedIn ? "/chat" : "/login"} state={signedIn ? undefined : { mode: "signup" }} className={btnPrimary}>
              {signedIn ? "Open app" : "Get started"}
              <ArrowRight size={16} />
            </Link>
            {!signedIn && (
              <Link to="/login" className={btnSecondary}>
                Sign in
              </Link>
            )}
          </div>
        </section>

        {/* Product preview */}
        <section className="mx-auto max-w-3xl px-4 pb-20" aria-label="Example conversation">
          <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
              <span className="h-2.5 w-2.5 rounded-full bg-border" />
              <span className="ml-3 inline-flex items-center gap-1.5 rounded-full border border-border bg-bg px-2.5 py-0.5 text-xs text-fg-muted">
                <Lock size={11} />
                prompt_engineering.pdf
              </span>
            </div>
            <div className="space-y-5 p-5 text-left text-[15px] leading-relaxed">
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl bg-bubble-user px-4 py-2.5 text-white">
                  What is a prompt?
                </div>
              </div>
              <div>
                <p>
                  A <strong>prompt</strong> is the input you give an AI model. It can include
                  instructions, questions, context, examples, constraints and a desired output
                  format.
                </p>
                <span className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-border bg-bg px-2.5 py-1 text-xs text-fg-muted">
                  <BookOpen size={12} className="text-accent" />
                  prompt_engineering.pdf · p. 2
                </span>
              </div>
            </div>
          </div>
          <p className="mt-3 text-center text-xs text-fg-muted">Illustrative example.</p>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-6xl px-4 pb-20" aria-labelledby="features-heading">
          <h2 id="features-heading" className="text-center text-2xl font-semibold sm:text-3xl">
            Built for trustworthy answers
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <div
                key={title}
                className="rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-accent/40"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-bg text-accent">
                  <Icon size={18} />
                </span>
                <h3 className="mt-4 font-medium">{title}</h3>
                <p className="mt-1.5 text-sm text-fg-muted">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="mx-auto max-w-4xl px-4 pb-20" aria-labelledby="how-heading">
          <h2 id="how-heading" className="text-center text-2xl font-semibold sm:text-3xl">
            How it works
          </h2>
          <ol className="mt-10 grid gap-6 sm:grid-cols-3">
            {STEPS.map((s) => (
              <li key={s.n} className="text-center">
                <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full border border-accent/40 bg-accent/10 text-sm font-semibold text-accent">
                  {s.n}
                </span>
                <h3 className="mt-3 font-medium">{s.title}</h3>
                <p className="mt-1 text-sm text-fg-muted">{s.text}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Final CTA */}
        <section className="mx-auto max-w-3xl px-4 pb-24">
          <div className="rounded-3xl border border-border bg-surface px-6 py-12 text-center">
            <h2 className="text-2xl font-semibold sm:text-3xl">Ready to ask your first question?</h2>
            <p className="mx-auto mt-3 max-w-md text-sm text-fg-muted">
              Create an account and start chatting with your documents in under a minute.
            </p>
            <Link
              to={signedIn ? "/chat" : "/login"}
              state={signedIn ? undefined : { mode: "signup" }}
              className={cn(btnPrimary, "mt-6")}
            >
              {signedIn ? "Open app" : "Get started"}
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs text-fg-muted sm:flex-row">
          <span>© {new Date().getFullYear()} RAG Chat</span>
          <span>Answers are generated by AI. Check the sources.</span>
        </div>
      </footer>
    </div>
  );
}