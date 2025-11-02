interface AddToTodayButtonProps {
  onAddToToday: (kind: "admin" | "work", tasks?: string[]) => void;
}

export function AddToTodayButton({ onAddToToday }: AddToTodayButtonProps) {
  return (
    <button
      onClick={() => onAddToToday("work")}
      className="rounded px-3 py-1 text-sm border hover:bg-gray-50"
    >
      Add to Today
    </button>
  );
}

