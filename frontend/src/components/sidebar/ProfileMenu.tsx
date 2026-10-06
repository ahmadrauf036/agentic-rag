import { useEffect, useRef, useState } from "react";
import { LogOut, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import UsageLine from "./UsageLine";

export default function ProfileMenu() {
  const { user, signOut } = useAuth();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleSignOut = async () => {
    setBusy(true);
    try {
      await signOut(); // ProtectedRoute redirects to /login
    } catch {
      toast.error("Could not sign out. Try again.");
      setBusy(false);
    }
  };

  const email = user?.email ?? "Account";

  return (
    <div ref={rootRef} className="relative border-t border-border p-2">
      {open && (
        <div
          role="menu"
          className="absolute inset-x-2 bottom-full mb-2 animate-pop-in rounded-xl border border-border bg-surface-2 p-3 shadow-xl"
        >
          <p className="text-xs text-fg-muted">Signed in as</p>
          <p className="mb-3 break-all text-sm">{email}</p>
          <UsageLine />

          <Button
            variant="secondary"
            size="sm"
            className="w-full"
            onClick={handleSignOut}
            disabled={busy}
            role="menuitem"
          >
            <LogOut size={14} />
            {busy ? "Signing out…" : "Sign out"}
          </Button>
        </div>
      )}

      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2.5 rounded-lg p-2 text-left transition-colors hover:bg-surface-2"
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bubble-user">
          <User size={16} />
        </span>
        <span className="min-w-0 flex-1 truncate text-sm">{email}</span>
      </button>
    </div>
  );
}