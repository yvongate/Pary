import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Désactiver Turbopack temporairement si bugs HMR
  // Pour utiliser webpack classique: npm run dev -- --no-turbopack
  
  reactStrictMode: true,
  
  // Configuration CORS pour l'API backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
