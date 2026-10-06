import { useNavigate } from "react-router-dom";
import { AlertCircle, FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Props {
  kind: "not-found" | "error";
  message?: string | null;
  onRetry: () => void;
}

export default function ChatError({ kind, message, onRetry }: Props) {
  const navigate = useNavigate();
  const notFound = kind === "not-found";
  const Icon = notFound ? FileQuestion : AlertCircle;

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-4 text-center">
      <Icon size={32} className={notFound ? "text-fg-muted" : "text-danger"} />
      <h2 className="text-lg font-semibold">
        {notFound ? "Chat not found" : "Couldn't load this chat"}
      </h2>
      <p className="max-w-sm text-sm text-fg-muted">
        {notFound
          ? "It may have been deleted, or it belongs to a different account."
          : message ?? "Something went wrong."}
      </p>
      <div className="mt-2 flex gap-2">
        {!notFound && (
          <Button variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        )}
        <Button onClick={() => navigate("/chat")}>Start a new chat</Button>
      </div>
    </div>
  );
}