import { useCallback, useState } from "react";
import { Outlet } from "react-router-dom";
import { PanelLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import Sidebar from "@/components/sidebar/Sidebar";
import { cn } from "@/lib/cn";

const isDesktop = () => window.matchMedia("(min-width: 768px)").matches;
export interface LayoutContext {
  sidebarOpen: boolean;
}
export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(isDesktop);

  // Mobile only: close the drawer after navigating
  const handleNavigate = useCallback(() => {
    if (!isDesktop()) setSidebarOpen(false);
  }, []);

  return (
    <div className="flex h-full overflow-hidden">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        inert={!sidebarOpen}
        className={cn(
          "z-40 flex h-full w-72 shrink-0 flex-col border-r border-border bg-surface",
          "transition-[margin,transform] duration-200",
          "max-md:fixed max-md:inset-y-0 max-md:left-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:-ml-72 md:translate-x-0",
        )}
      >
        <Sidebar onHide={() => setSidebarOpen(false)} onNavigate={handleNavigate} />
      </aside>

      <div className="relative flex min-w-0 flex-1 flex-col">
        {!sidebarOpen && (
          <Button
            size="icon"
            variant="ghost"
            aria-label="Show sidebar"
            className="absolute left-3 top-3 z-20"
            onClick={() => setSidebarOpen(true)}
          >
            <PanelLeft size={18} />
          </Button>
        )}
        <Outlet  context={{sidebarOpen} satisfies LayoutContext}/>
      </div>
    </div>
  );
}