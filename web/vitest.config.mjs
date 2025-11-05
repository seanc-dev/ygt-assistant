import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react({
      jsxRuntime: "automatic",
    }),
  ],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
  },
  resolve: {
    alias: {
      react: path.resolve(__dirname, "./node_modules/react"),
      "react-dom": path.resolve(__dirname, "./node_modules/react-dom"),
      "@lucid-work/ui": path.resolve(__dirname, "../shared-ui/src"),
      // Resolve shared-ui dependencies from web/node_modules
      clsx: path.resolve(__dirname, "./node_modules/clsx"),
    },
  },
  optimizeDeps: {
    include: ["react", "react-dom", "clsx"],
  },
});


