import { render, fireEvent } from "@testing-library/react";
import ReviewPage from "../pages/review";

// minimal smoke test for keybindings; environment may need Next.js test setup
it("handles keyboard shortcuts without crashing", () => {
  const { container } = render(<ReviewPage /> as any);
  fireEvent.keyDown(window, { key: "a" });
  fireEvent.keyDown(window, { key: "e" });
  fireEvent.keyDown(window, { key: "s" });
  fireEvent.keyDown(window, { key: "u" });
  expect(container).toBeTruthy();
});
