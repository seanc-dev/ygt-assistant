export type AttachedDoc = {
  id: string;
  title: string;
  placeholder: boolean;
  createdAt: string;
};

export type ContextSpace = {
  notes: string[];
  decisions: string[];
  constraints: string[];
  docs: AttachedDoc[];
};

export type ContextCommandId = "note" | "decision" | "constraint" | "doc";

export type UpdateContextSpace = (
  updater: (space: ContextSpace) => ContextSpace
) => void;

export const createEmptyContextSpace = (): ContextSpace => ({
  notes: [],
  decisions: [],
  constraints: [],
  docs: [],
});

const createPlaceholderDoc = (title: string): AttachedDoc => ({
  id: `doc-${Math.random().toString(36).slice(2, 10)}`,
  title,
  placeholder: true,
  createdAt: new Date().toISOString(),
});

export const applyContextCommand = ({
  commandId,
  inputValue,
  updateContextSpace,
}: {
  commandId: string;
  inputValue: string;
  updateContextSpace: UpdateContextSpace;
}): boolean => {
  const trimmed = inputValue.trim();
  if (!trimmed) {
    return false;
  }

  switch (commandId) {
    case "note": {
      updateContextSpace((space) => ({
        ...space,
        notes: [...space.notes, trimmed],
      }));
      return true;
    }
    case "decision": {
      updateContextSpace((space) => ({
        ...space,
        decisions: [...space.decisions, trimmed],
      }));
      return true;
    }
    case "constraint": {
      updateContextSpace((space) => ({
        ...space,
        constraints: [...space.constraints, trimmed],
      }));
      return true;
    }
    case "doc": {
      updateContextSpace((space) => ({
        ...space,
        docs: [...space.docs, createPlaceholderDoc(trimmed)],
      }));
      return true;
    }
    default:
      return false;
  }
};

