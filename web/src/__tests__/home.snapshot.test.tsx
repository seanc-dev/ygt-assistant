import { render } from "@testing-library/react";
import Home from "../pages";

it("renders Home without crashing", () => {
  const { container } = render(<Home /> as any);
  expect(container).toBeTruthy();
});
