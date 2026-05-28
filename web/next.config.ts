import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so FastAPI can serve the bundled UI from the same origin
  output: "export",
  // Backend SSE endpoint base — overridable per environment
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE ?? "",
  },
};

export default nextConfig;
