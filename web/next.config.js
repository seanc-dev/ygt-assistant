/** @type {import('next').NextConfig} */
const path = require("path");

const ADMIN_API_BASE =
  process.env.NEXT_PUBLIC_ADMIN_API_BASE ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://api.coachflow.nz");

const normalizedAdminApiBase = ADMIN_API_BASE.replace(/\/+$/, "");

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@lucid-work/ui"],
  // Ensure Next.js treats this folder as the root to avoid mixed lockfile/module resolution
  outputFileTracingRoot: __dirname,
  experimental: {
    // Allow Next.js to resolve files outside the project root (for shared-ui symlink)
    externalDir: true,
  },
  async rewrites() {
    return [
      {
        source: "/__admin_api/:path*",
        destination: `${normalizedAdminApiBase}/:path*`,
      },
    ];
  },
  webpack: (config, { isServer }) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
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
      // Explicit alias for @lucid-work/ui to ensure proper resolution
      // Use node_modules symlink path so it resolves within project boundary
      "@lucid-work/ui": path.resolve(__dirname, "../node_modules/@lucid-work/ui/src"),
    };
    
    // Ensure shared-ui TypeScript files are transpiled
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    
    return config;
  },
};
module.exports = nextConfig;

// Trigger redeploy: config noop comment
