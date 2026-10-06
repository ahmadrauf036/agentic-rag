import { useCallback, useEffect, useMemo, useState } from "react";
import { Info, Search, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tooltip } from "@/components/ui/ToolTip";
import RoleBadge from "@/components/admin/RoleBadge";
import { formatDateTime } from "@/lib/date";
import type { AdminUser, Role } from "@/types";

export default function UsersTab() {
  const { user: me } = useAuth();
  const toast = useToast();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const [target, setTarget] = useState<{ user: AdminUser; role: Role } | null>(null);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.admin.users();
      setUsers([...list].sort((a, b) => a.email.localeCompare(b.email)));
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 403
          ? "Admin access required."
          : e instanceof Error
            ? e.message
            : "Failed to load users",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? users.filter((u) => u.email.toLowerCase().includes(q)) : users;
  }, [users, query]);

  const confirm = async () => {
    if (!target) return;
    setSaving(true);
    try {
      const res = await api.admin.setRole(target.user.id, target.role);
      setUsers((prev) =>
        prev.map((u) => (u.id === res.user_id ? { ...u, role: res.new_role } : u)),
      );
      setNotice(
        `${target.user.email} is now ${res.new_role === "admin" ? "an admin" : "a regular user"}. ` +
          "They must sign out and back in before the change takes effect.",
      );
      toast.success("Role updated");
      setTarget(null);
    } catch (e) {
      // 400 covers invalid role and self-demotion; show the backend text
      toast.error(e instanceof Error ? e.message : "Could not change role");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {notice && (
        <div
          role="status"
          className="flex items-start gap-2.5 rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm"
        >
          <Info size={16} className="mt-0.5 shrink-0 text-accent" />
          <p className="flex-1">{notice}</p>
          <button
            type="button"
            aria-label="Dismiss"
            onClick={() => setNotice(null)}
            className="rounded p-0.5 text-fg-muted hover:text-fg"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <div className="relative max-w-sm">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted"
        />
        <Input
          type="search"
          placeholder="Search by email"
          aria-label="Search users by email"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-8 [&::-webkit-search-cancel-button]:hidden"
        />
      </div>

      {error ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center text-sm">
          <p className="text-danger">{error}</p>
          <Button variant="secondary" size="sm" className="mt-3" onClick={load}>
            Retry
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full min-w-160 border-collapse text-left text-sm">
            <thead className="bg-surface text-xs text-fg-muted">
              <tr>
                <th className="px-4 py-2.5 font-medium">Email</th>
                <th className="px-4 py-2.5 font-medium">Role</th>
                <th className="px-4 py-2.5 font-medium">Created</th>
                <th className="px-4 py-2.5 font-medium">Last sign-in</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                [0, 1, 2, 3].map((i) => (
                  <tr key={i} aria-hidden="true">
                    {[0, 1, 2, 3, 4].map((c) => (
                      <td key={c} className="px-4 py-3">
                        <Skeleton className="h-4 w-full max-w-36" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-fg-muted">
                    {users.length === 0 ? "No users found." : `No users match “${query.trim()}”.`}
                  </td>
                </tr>
              ) : (
                filtered.map((u) => {
                  const isSelf = u.id === me?.id;
                  const next: Role = u.role === "admin" ? "user" : "admin";
                  const button = (
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={isSelf}
                      onClick={() => setTarget({ user: u, role: next })}
                    >
                      {next === "admin" ? "Make admin" : "Make user"}
                    </Button>
                  );
                  return (
                    <tr key={u.id} className="hover:bg-surface/60">
                      <td className="px-4 py-3">
                        <span className="break-all">{u.email}</span>
                        {isSelf && <span className="ml-2 text-xs text-fg-muted">(you)</span>}
                      </td>
                      <td className="px-4 py-3">
                        <RoleBadge role={u.role} />
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-fg-muted">
                        {formatDateTime(u.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-fg-muted">
                        {formatDateTime(u.last_sign_in_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {isSelf ? (
                          <Tooltip label="You can't change your own role" side="bottom">
                            <span tabIndex={0}>{button}</span>
                          </Tooltip>
                        ) : (
                          button
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={target !== null}
        onClose={() => !saving && setTarget(null)}
        title={target?.role === "admin" ? "Make this user an admin?" : "Remove admin access?"}
        className="max-w-sm"
      >
        <p className="text-sm text-fg-muted">
          <span className="break-all text-fg">{target?.user.email}</span>{" "}
          {target?.role === "admin"
            ? "will be able to upload and delete documents and manage other users."
            : "will lose access to the admin area, uploads, and deletes."}
        </p>
        <p className="mt-2 text-sm text-fg-muted">
          The change applies after they sign out and back in.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" disabled={saving} onClick={() => setTarget(null)}>
            Cancel
          </Button>
          <Button
            variant={target?.role === "admin" ? "primary" : "danger"}
            disabled={saving}
            onClick={confirm}
          >
            {saving ? "Saving…" : "Confirm"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}