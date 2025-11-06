interface WorkloadStatsProps {
  triaged: number;
  completed: number;
}

/**
 * Display weekly triaged and completed stats.
 */
export function WorkloadStats({ triaged, completed }: WorkloadStatsProps) {
  const completionRate = triaged > 0 ? Math.round((completed / triaged) * 100) : 0;
  
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-slate-600">
        <span className="font-medium text-slate-900">{triaged}</span> triaged
      </span>
      <span className="text-slate-400">/</span>
      <span className="text-slate-600">
        <span className="font-medium text-slate-900">{completed}</span> completed
      </span>
      {triaged > 0 && (
        <>
          <span className="text-slate-400">/</span>
          <span className="text-slate-600">
            <span className="font-medium text-slate-900">{completionRate}%</span>
          </span>
        </>
      )}
    </div>
  );
}

