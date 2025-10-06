/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@coachflow/ui"],
};
module.exports = nextConfig;

// Trigger redeploy: config noop comment
