/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@ygt-assistant/ui"],
  // Ensure Next.js treats this folder as the root to avoid mixed lockfile/module resolution
  experimental: {
    outputFileTracingRoot: __dirname,
  },
};
module.exports = nextConfig;

// Trigger redeploy: config noop comment
