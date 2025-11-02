interface DeferMenuProps {
  onDefer: (bucket: string) => void;
}

export function DeferMenu({ onDefer }: DeferMenuProps) {
  return (
    <div className="rounded-lg border p-2">
      <div className="mb-2 text-xs font-medium">Defer</div>
      <div className="space-y-1">
        <button
          onClick={() => onDefer("afternoon")}
          className="block w-full text-left text-xs px-2 py-1 hover:bg-gray-100"
        >
          Afternoon
        </button>
        <button
          onClick={() => onDefer("tomorrow")}
          className="block w-full text-left text-xs px-2 py-1 hover:bg-gray-100"
        >
          Tomorrow
        </button>
        <button
          onClick={() => onDefer("this_week")}
          className="block w-full text-left text-xs px-2 py-1 hover:bg-gray-100"
        >
          This Week
        </button>
        <button
          onClick={() => onDefer("next_week")}
          className="block w-full text-left text-xs px-2 py-1 hover:bg-gray-100"
        >
          Next Week
        </button>
      </div>
    </div>
  );
}

