import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import type { RefObject } from "react";
import { TokenOverlay } from "../TokenOverlay";
import type { TokenSegment } from "../types";

describe("TokenOverlay", () => {
  it("shows placeholder when message is empty", () => {
    const ref: RefObject<HTMLDivElement> = { current: document.createElement("div") };
    render(
      <TokenOverlay
        message=""
        tokenSegments={[]}
        activeTokenDetailId={null}
        tokenOverlayRef={ref}
        onToggleDetail={vi.fn()}
        onRemoveToken={vi.fn()}
      />
    );
    expect(screen.getByText("Message Assistant")).toBeInTheDocument();
  });

  it("renders tokens and handles actions", () => {
    const ref: RefObject<HTMLDivElement> = { current: document.createElement("div") };
    const segments: TokenSegment[] = [
      { type: "text", text: "Do " },
      {
        type: "token",
        token: {
          raw: '[ref v:1 type:"task" id:"t-1" name:"Task"]',
          kind: "ref",
          label: "task: Task",
          start: 3,
          end: 45,
          data: { name: "Task", id: "t-1" },
        },
      },
    ];
    const onToggleDetail = vi.fn();
    const onRemoveToken = vi.fn();

    render(
      <TokenOverlay
        message="Do [ref ...]"
        tokenSegments={segments}
        activeTokenDetailId={null}
        tokenOverlayRef={ref}
        onToggleDetail={onToggleDetail}
        onRemoveToken={onRemoveToken}
      />
    );

    const chip = screen.getByText("task: Task");
    fireEvent.click(chip);
    expect(onToggleDetail).toHaveBeenCalled();

    const removeButton = screen.getByLabelText("Remove token");
    fireEvent.click(removeButton);
    expect(onRemoveToken).toHaveBeenCalled();
  });
});

