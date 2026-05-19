/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiEndpoint =
      process.env.NEXT_PUBLIC_API_ENDPOINT ||
      "http://localhost:4566/restapis/default/_user_request_";
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${apiEndpoint}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
