import type { WorkloadRating } from "../../lib/workload.js";

interface WorkloadStatusProps {
  rating: WorkloadRating;
}

/**
 * Display workload rating as a badge.
 */
export function WorkloadStatus({ rating }: WorkloadStatusProps) {
  const labels: Record<WorkloadRating, string> = {
    manageable: "Manageable workload",
    rising: "Rising workload",
    overloaded: "Overloaded workload",
  };
  
  const colors: Record<WorkloadRating, string> = {
    manageable: "bg-emerald-100 text-emerald-700 border-emerald-200",
    rising: "bg-amber-100 text-amber-700 border-amber-200",
    overloaded: "bg-rose-100 text-rose-700 border-rose-200",
  };
  
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border
        ${colors[rating]}
      `}
      aria-label={`Workload status: ${labels[rating]}`}
    >
      {labels[rating]}
    </span>
  );
}

