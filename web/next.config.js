/** @type {import('next').NextConfig} */
const path = require("path");

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@ygt-assistant/ui"],
  // Ensure Next.js treats this folder as the root to avoid mixed lockfile/module resolution
  experimental: {
    outputFileTracingRoot: __dirname,
  },
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
    };
    return config;
  },
};
module.exports = nextConfig;

// Trigger redeploy: config noop comment
