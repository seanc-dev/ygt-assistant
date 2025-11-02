interface AltPlansPanelProps {
  plans: Array<{
    id: string;
    type: string;
    blocks: Array<{
      id: string;
      kind: string;
      start: string;
      end: string;
    }>;
  }>;
  overload?: {
    detected: boolean;
    proposals?: Array<{
      type: string;
      target_id: string;
      reason: string;
      requires_approval: boolean;
    }>;
  };
}

export function AltPlansPanel({ plans, overload }: AltPlansPanelProps) {
  const formatTime = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="rounded-lg border p-4 space-y-4">
      <div className="font-medium">Alternative Schedule Plans</div>
      
      {plans.map((plan) => (
        <div key={plan.id} className="border rounded p-3">
          <div className="font-medium text-sm mb-2 capitalize">
            {plan.type.replace("-", " ")}
          </div>
          <div className="space-y-1">
            {plan.blocks.length === 0 ? (
              <div className="text-xs text-gray-500">No blocks in this plan</div>
            ) : (
              plan.blocks.map((block) => (
                <div key={block.id} className="text-xs">
                  {formatTime(block.start)} - {formatTime(block.end)}: {block.kind}
                </div>
              ))
            )}
          </div>
        </div>
      ))}

      {overload?.detected && overload.proposals && overload.proposals.length > 0 && (
        <div className="border-t pt-3 mt-3">
          <div className="font-medium text-sm text-orange-600 mb-2">
            Overload Detected - Action Required
          </div>
          <div className="space-y-1">
            {overload.proposals.map((proposal, idx) => (
              <div key={idx} className="text-xs">
                <span className="font-medium capitalize">{proposal.type}:</span>{" "}
                {proposal.reason}
                {proposal.requires_approval && (
                  <span className="text-orange-600 ml-1">(Requires approval)</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
