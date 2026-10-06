import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { LayoutContext } from "@/components/AppLayout";
import OverviewTab from "@/components/admin/OverviewTab";
import UsersTab from "@/components/admin/UsersTab";
import SessionsTab, { type SessionFilter } from "@/components/admin/SessionsTab";
import DocumentsTab from "@/components/admin/DocumentsTab";
import { cn } from "@/lib/cn";

import UsageTab from "@/components/admin/UsageTab";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "users", label: "Users" },
  { id: "documents", label: "Documents" },
  { id: "sessions", label: "Chats" },
  { id: "usage", label: "Usage" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function AdminPage() {
  const { sidebarOpen } = useOutletContext<LayoutContext>();
  const [tab, setTab] = useState<TabId>("overview");
  const [sessionFilter, setSessionFilter] = useState<SessionFilter>("all");

  const selectTab = (id: TabId) => {
    if (id === "sessions") setSessionFilter("all");
    setTab(id);
  };

  return (
    <main className="flex h-full min-h-0 flex-col">
      <header
        className={cn(
          "flex h-14 shrink-0 items-center border-b border-border pr-4",
          "transition-[padding] duration-200",
          sidebarOpen ? "pl-4" : "pl-14",
        )}
      >
        <h1 className="text-sm font-medium">Admin</h1>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-5xl px-4 py-6">
          <div
            role="tablist"
            aria-label="Admin sections"
            className="mb-5 flex gap-1 overflow-x-auto border-b border-border"
          >
            {TABS.map((t) => (
              <button
                key={t.id}
                role="tab"
                type="button"
                aria-selected={tab === t.id}
                onClick={() => selectTab(t.id)}
                className={cn(
                  "-mb-px shrink-0 border-b-2 px-3 py-2 text-sm transition-colors",
                  tab === t.id
                    ? "border-accent text-fg"
                    : "border-transparent text-fg-muted hover:text-fg",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div role="tabpanel">
            {tab === "overview" && (
              <OverviewTab
                onViewPaused={() => {
                  setSessionFilter("paused");
                  setTab("sessions");
                }}
              />
            )}
            {tab === "users" && <UsersTab />}
            {tab === "documents" && <DocumentsTab />}
            {tab === "sessions" && <SessionsTab key={sessionFilter} initialFilter={sessionFilter} />}
            {tab === "usage" && <UsageTab />}
          </div>
        </div>
      </div>
    </main>
  );
}