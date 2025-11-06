import type { WorkloadRating } from "../../../lib/workload";

interface WorkloadStatusProps {
  rating: WorkloadRating;
}

/**
 * Display workload rating as a small, calm badge.
 */
export function WorkloadStatus({ rating }: WorkloadStatusProps) {
  const labels: Record<WorkloadRating, string> = {
    manageable: "Manageable workload",
    rising: "Rising workload",
    overloaded: "Overloaded workload",
  };
  
  const styles: Record<WorkloadRating, string> = {
    manageable: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    rising: "bg-amber-50 text-amber-700 ring-amber-100",
    overloaded: "bg-rose-50 text-rose-700 ring-rose-100",
  };
  
  return (
    <span
      className={`
        inline-flex items-center rounded-full px-2.5 py-1 text-xs ring-1
        ${styles[rating]}
      `}
      aria-label={`Workload status: ${labels[rating]}`}
    >
      {labels[rating]}
    </span>
  );
}
