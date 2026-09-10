import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    "react-force-graph-2d",
    "react-force-graph-3d",
    "3d-force-graph",
    "force-graph",
  ],
};

export default nextConfig;
