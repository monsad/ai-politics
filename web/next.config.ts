import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/app",
  assetPrefix: "/app",
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE ?? "",
  },
};

export default nextConfig;
