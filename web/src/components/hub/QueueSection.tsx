import { ReactNode } from "react";

interface QueueSectionProps {
  title: string;
  count: number;
  children: ReactNode;
}

export function QueueSection({ title, count, children }: QueueSectionProps) {
  return (
    <div className="mt-8 first:mt-0">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">
        {title} ({count})
      </h3>
      {children}
    </div>
  );
}
