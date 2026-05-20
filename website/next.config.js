const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      // Fallback: ensure @/* resolves even if Amplify appRoot drifts.
      "@": path.resolve(__dirname),
    };

    return config;
  },
};

module.exports = nextConfig;
