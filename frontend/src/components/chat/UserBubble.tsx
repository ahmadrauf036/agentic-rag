import { memo } from "react";
import { Copy, Pencil } from "lucide-react";
import ActionButton, { ACTIONS_ROW } from "@/components/chat/ActionButton";
import { useToast } from "@/components/ui/Toast";
import { copyText } from "@/lib/clipboard";

interface Props {
  content: string;
  onEdit: (text: string) => void;
}

const UserBubble = memo(function UserBubble({ content, onEdit }: Props) {
  const toast = useToast();

  const copy = async () =>
    (await copyText(content)) ? toast.success("Copied") : toast.error("Could not copy");

  return (
    <div className="group flex flex-col items-end">
      <div className="max-w-[85%] whitespace-pre-wrap wrap-break-word rounded-2xl bg-bubble-user px-4 py-2.5 text-[15px] text-white">
        {content}
      </div>
      <div className={ACTIONS_ROW}>
        <ActionButton label="Edit" onClick={() => onEdit(content)}>
          <Pencil size={14} />
        </ActionButton>
        <ActionButton label="Copy" onClick={copy}>
          <Copy size={14} />
        </ActionButton>
      </div>
    </div>
  );
});

export default UserBubble;