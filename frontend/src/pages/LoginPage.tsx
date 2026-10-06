import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

type Mode = "signin" | "signup";

export default function LoginPage() {
  const { session, loading } = useAuth();
  const location = useLocation();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Already signed in: go where they were headed (or /chat)
  if (!loading && session) {
    const from = (location.state as { from?: string } | null)?.from ?? "/chat";
    return <Navigate to={from} replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);

    try {
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        // AuthContext picks up the session; the redirect above handles navigation.
      } else {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (!data.session) {
          // Email confirmation is enabled in Supabase
          setNotice("Check your email for a confirmation link, then sign in.");
          setMode("signin");
          setPassword("");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const isSignup = mode === "signup";

  return (
    <main className="flex min-h-full items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-6">
        <h1 className="text-xl font-semibold">{isSignup ? "Create account" : "Welcome back"}</h1>
        <p className="mt-1 text-sm text-fg-muted">
          {isSignup ? "Sign up to start chatting with your documents." : "Sign in to continue."}
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-3">
          <Input
            type="email"
            required
            autoComplete="email"
            placeholder="Email"
            aria-label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            required
            minLength={6}
            autoComplete={isSignup ? "new-password" : "current-password"}
            placeholder="Password"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          )}
          {notice && <p className="text-sm text-accent">{notice}</p>}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Please wait…" : isSignup ? "Sign up" : "Sign in"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-fg-muted">
          {isSignup ? "Already have an account?" : "New here?"}{" "}
          <button
            type="button"
            className="text-accent hover:underline"
            onClick={() => {
              setMode(isSignup ? "signin" : "signup");
              setError(null);
              setNotice(null);
            }}
          >
            {isSignup ? "Sign in" : "Create an account"}
          </button>
        </p>
      </div>
    </main>
  );
}