/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Enable for Docker
  images: {
    domains: ['image.tmdb.org'], // For future TMDB poster images
  },
}

module.exports = nextConfig
