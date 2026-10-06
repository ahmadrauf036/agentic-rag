import { Skeleton } from "@/components/ui/Skeleton";

export default function MessageListSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Loading messages">
      {[0, 1].map((i) => (
        <div key={i} className="space-y-8">
          <div className="flex justify-end">
            <Skeleton className="h-10 w-2/5 rounded-2xl" />
          </div>
          <div className="space-y-2.5">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}