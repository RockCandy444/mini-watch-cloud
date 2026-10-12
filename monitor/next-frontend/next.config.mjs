const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${process.env.MONITOR_API_URL || "http://monitor-api:5000"}/api/:path*` },
      { source: "/general-api/:path*", destination: "http://monitor-api:5000/general-api/:path*" },
    ];
  },
};

export default nextConfig;
