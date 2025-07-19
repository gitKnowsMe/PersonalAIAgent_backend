/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features
  experimental: {
    serverComponentsExternalPackages: []
  },

  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`
      }
    ]
  },

  // CORS configuration for API communication
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ]
  },

  // Output configuration for Vercel deployment
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  // Image optimization
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },

  // Webpack configuration
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Add any custom webpack configuration here
    return config
  },

  // Environment variables to expose to the browser
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/',
        destination: '/chat',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig