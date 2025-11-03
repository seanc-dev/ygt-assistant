import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
  },
  resolve: {
    alias: {
      react: path.resolve(process.cwd(), "./node_modules/react"),
      "react-dom": path.resolve(process.cwd(), "./node_modules/react-dom"),
      "react/jsx-runtime": path.resolve(process.cwd(), "./node_modules/react/jsx-runtime.js"),
      "react/jsx-dev-runtime": path.resolve(process.cwd(), "./node_modules/react/jsx-dev-runtime.js"),
      "@ygt-assistant/ui": path.resolve(process.cwd(), "../shared-ui/src"),
    },
  },
});
