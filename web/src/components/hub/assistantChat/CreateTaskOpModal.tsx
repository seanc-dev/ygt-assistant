import { useEffect, useState } from "react";
import type { ProjectOption } from "./types";
import { ModalShell } from "./ModalShell";

export type CreateTaskOpModalProps = {
  projects: ProjectOption[];
  initialProjectId?: string | null;
  onSubmit: (payload: { projectId: string; title: string }) => void;
  onClose: () => void;
};

export function CreateTaskOpModal({
  projects,
  initialProjectId,
  onSubmit,
  onClose,
}: CreateTaskOpModalProps) {
  const [projectId, setProjectId] = useState<string>(
    initialProjectId && projects.some((p) => p.id === initialProjectId)
      ? initialProjectId
      : projects[0]?.id || ""
  );
  const [title, setTitle] = useState("");

  useEffect(() => {
    if (
      initialProjectId &&
      projects.some((project) => project.id === initialProjectId)
    ) {
      setProjectId(initialProjectId);
    }
  }, [initialProjectId, projects]);

  return (
    <ModalShell title="Create task operation" onClose={onClose}>
      {projects.length === 0 ? (
        <p className="text-sm text-slate-600">
          You need at least one project to create a task operation.
        </p>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!title.trim()) return;
            onSubmit({ projectId, title: title.trim() });
          }}
          className="space-y-4"
        >
          <div>
            <label className="text-sm font-medium text-slate-700">
              Project
            </label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">
              Task title
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Draft executive summary"
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Insert op
            </button>
          </div>
        </form>
      )}
    </ModalShell>
  );
}

