/** @type {import('next').NextConfig} */
const path = require("path");

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@ygt-assistant/ui"],
  // Ensure Next.js treats this folder as the root to avoid mixed lockfile/module resolution
  outputFileTracingRoot: __dirname,
  webpack: (config, { isServer }) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "react/jsx-runtime": path.resolve(
        __dirname,
        "node_modules/react/jsx-runtime.js"
      ),
      "react/jsx-dev-runtime": path.resolve(
        __dirname,
        "node_modules/react/jsx-dev-runtime.js"
      ),
      // Explicit alias for @ygt-assistant/ui to ensure proper resolution
      "@ygt-assistant/ui": path.resolve(__dirname, "../shared-ui/src"),
    };
    
    // Ensure shared-ui TypeScript files are transpiled
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    
    return config;
  },
};
module.exports = nextConfig;

// Trigger redeploy: config noop comment
