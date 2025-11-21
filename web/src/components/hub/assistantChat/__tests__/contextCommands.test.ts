import { describe, expect, it, vi } from "vitest";
import {
  applyContextCommand,
  createEmptyContextSpace,
  type ContextSpace,
} from "../contextCommands";

describe("applyContextCommand", () => {
  const createUpdater = (initial?: ContextSpace) => {
    let space = initial ?? createEmptyContextSpace();
    const updateContextSpace = vi.fn((updater: (ctx: ContextSpace) => ContextSpace) => {
      space = updater(space);
    });
    return { updateContextSpace, getSpace: () => space };
  };

  it("appends notes, decisions, and constraints to context", () => {
    const { updateContextSpace, getSpace } = createUpdater();

    const noteHandled = applyContextCommand({
      commandId: "note",
      inputValue: "Remember to sync with design",
      updateContextSpace,
    });
    const decisionHandled = applyContextCommand({
      commandId: "decision",
      inputValue: "Ship with the compact layout",
      updateContextSpace,
    });
    const constraintHandled = applyContextCommand({
      commandId: "constraint",
      inputValue: "Keep offline support in mind",
      updateContextSpace,
    });

    expect(noteHandled).toBe(true);
    expect(decisionHandled).toBe(true);
    expect(constraintHandled).toBe(true);

    const space = getSpace();
    expect(space.notes).toEqual(["Remember to sync with design"]);
    expect(space.decisions).toEqual(["Ship with the compact layout"]);
    expect(space.constraints).toEqual(["Keep offline support in mind"]);
  });

  it("creates placeholder docs when handling /doc", () => {
    const { updateContextSpace, getSpace } = createUpdater();

    const handled = applyContextCommand({
      commandId: "doc",
      inputValue: "QA checklist",
      updateContextSpace,
    });

    expect(handled).toBe(true);
    const space = getSpace();
    expect(space.docs).toHaveLength(1);
    expect(space.docs[0]).toMatchObject({
      title: "QA checklist",
      placeholder: true,
    });
    expect(space.docs[0].id).toMatch(/^doc-/);
  });

  it("ignores empty input", () => {
    const { updateContextSpace } = createUpdater();

    const handled = applyContextCommand({
      commandId: "note",
      inputValue: "   ",
      updateContextSpace,
    });

    expect(handled).toBe(false);
    expect(updateContextSpace).not.toHaveBeenCalled();
  });

  it("returns false for unsupported commands", () => {
    const { updateContextSpace } = createUpdater();

    const handled = applyContextCommand({
      commandId: "unknown",
      inputValue: "Should not be applied",
      updateContextSpace,
    });

    expect(handled).toBe(false);
    expect(updateContextSpace).not.toHaveBeenCalled();
  });
});
