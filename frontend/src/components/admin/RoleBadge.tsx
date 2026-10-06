import { Shield, User } from "lucide-react";
import { cn } from "@/lib/cn";
import type { Role } from "@/types";

export default function RoleBadge({ role }: { role: Role }) {
  const admin = role === "admin";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
        admin
          ? "border-accent/40 bg-accent/10 text-accent"
          : "border-border bg-surface text-fg-muted",
      )}
    >
      {admin ? <Shield size={11} /> : <User size={11} />}
      {admin ? "Admin" : "User"}
    </span>
  );
}