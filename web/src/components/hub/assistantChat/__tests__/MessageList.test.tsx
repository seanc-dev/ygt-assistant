import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MessageList } from "../MessageList";
import type { MessageView } from "../types";

describe("MessageList", () => {
  const baseProps = {
    messageViews: [] as MessageView[],
    isTyping: false,
    onRetryMessage: vi.fn(),
    onEmbedUpdate: vi.fn(),
    animatedRef: { current: new Set<string>() },
    activeAssistantId: null as string | null,
    onInvokeSurfaceOp: vi.fn(),
    onNavigateSurface: vi.fn(),
  };

  it("renders empty state when there are no messages", () => {
    render(<MessageList {...baseProps} />);
    expect(
      screen.getByText("No messages yet. Start the conversation!")
    ).toBeInTheDocument();
  });

  it("shows typing indicator", () => {
    const { container } = render(<MessageList {...baseProps} isTyping />);
    expect(container.querySelectorAll(".animate-bounce").length).toBeGreaterThan(
      0
    );
  });
});

