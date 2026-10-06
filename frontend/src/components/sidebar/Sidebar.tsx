import { NavLink, useNavigate } from "react-router-dom";
import { PanelLeft, Plus, Shield } from "lucide-react";
import { Button } from "@/components/ui/Button";
import SessionList from "@/components/sidebar/SessionList";
import ProfileMenu from "@/components/sidebar/ProfileMenu";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/cn";

interface Props {
  onHide: () => void;
  /** Called after any navigation from the sidebar (closes the drawer on mobile). */
  onNavigate: () => void;
}

export default function Sidebar({ onHide, onNavigate }: Props) {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const newChat = () => {
    // Every navigate() produces a fresh location.key, so ChatPage can use it
    // to reset selection state even when we're already on /chat.
    navigate("/chat");
    onNavigate();
  };

  return (
    <>
      <div className="flex items-center justify-between p-3">
        <span className="px-1 text-base font-semibold tracking-tight">RAG Chat</span>
        <Button size="icon" variant="ghost" aria-label="Hide sidebar" onClick={onHide}>
          <PanelLeft size={18} />
        </Button>
      </div>

      <div className="px-3 pb-3">
        <Button variant="secondary" className="w-full justify-start" onClick={newChat}>
          <Plus size={16} />
          New chat
        </Button>
      </div>

      <SessionList onNavigate={onNavigate} />
      {isAdmin && (
  <div className="border-t border-border p-2">
    <NavLink
      to="/admin"
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-surface-2 text-fg shadow-[inset_2px_0_0_var(--color-accent)]"
            : "text-fg-muted hover:bg-surface-2/60 hover:text-fg",
        )
      }
    >
      <Shield size={16} />
      Admin
    </NavLink>
  </div>
)}
      <ProfileMenu />
    </>
  );
}