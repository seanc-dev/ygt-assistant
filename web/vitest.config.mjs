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
      // Force a single React copy (tests were pulling both 19.1 and 19.2)
      react: path.resolve(__dirname, "../node_modules/react"),
      "react-dom": path.resolve(__dirname, "../node_modules/react-dom"),
      "react/jsx-runtime": path.resolve(
        __dirname,
        "../node_modules/react/jsx-runtime.js"
      ),
      "react/jsx-dev-runtime": path.resolve(
        __dirname,
        "../node_modules/react/jsx-dev-runtime.js"
      ),
      "@lucid-work/ui": path.resolve(__dirname, "../shared-ui/src"),
      // Keep old alias for backward compatibility during transition
      "@ygt-assistant/ui": path.resolve(__dirname, "../shared-ui/src"),
      zustand: path.resolve(__dirname, "./src/test-utils/zustandShim.ts"),
      // Allow importing from pages and data directories in tests
      "@/pages": path.resolve(__dirname, "./src/pages"),
      "@/data": path.resolve(__dirname, "./src/data"),
    },
    // Ensure node_modules resolution works for shared-ui files
    // Look in both web and root node_modules for workspace dependencies
    // This allows clsx and other shared-ui deps to be resolved correctly
    modules: [
      path.resolve(__dirname, "./node_modules"),
      path.resolve(__dirname, "../node_modules"),
      "node_modules",
    ],
    dedupe: ["react", "react-dom", "react/jsx-runtime", "react/jsx-dev-runtime", "clsx"],
  },
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react/jsx-runtime",
      "react/jsx-dev-runtime",
      "clsx",
    ],
  },
});


