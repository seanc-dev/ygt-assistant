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
    pool: "forks",
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    testTimeout: 30000,
    hookTimeout: 30000,
    // Increase memory limits for large component tests
    isolate: false, // Disable isolation to reduce memory overhead
    // Exclude Playwright e2e tests - they should be run separately
    exclude: ["**/node_modules/**", "**/dist/**", "**/tests/e2e/**"],
  },
  resolve: {
    alias: {
      react: path.resolve(__dirname, "./node_modules/react"),
      "react-dom": path.resolve(__dirname, "./node_modules/react-dom"),
      "@ygt-assistant/ui": path.resolve(__dirname, "../shared-ui/src"),
      // Resolve shared-ui dependencies from web/node_modules
      clsx: path.resolve(__dirname, "./node_modules/clsx"),
      zustand: path.resolve(__dirname, "./src/test-utils/zustandShim.ts"),
      // Allow importing from pages and data directories in tests
      "@/pages": path.resolve(__dirname, "./src/pages"),
      "@/data": path.resolve(__dirname, "./src/data"),
    },
  },
  optimizeDeps: {
    include: ["react", "react-dom", "clsx"],
  },
});


