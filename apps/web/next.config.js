/** @type {import('next').NextConfig} */
// The browser calls /api/* on this server, which proxies to the API.
// In Docker the API is another container, so INTERNAL_API_URL points there.
const apiUrl = process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000'

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
