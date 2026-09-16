import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const noStore = [{ key: "Cache-Control", value: "no-cache, no-store, must-revalidate" }];

export default function config(phase: string): NextConfig {
  const isDev = phase === PHASE_DEVELOPMENT_SERVER;

  return {
    reactStrictMode: true,
    poweredByHeader: false,
    compress: true,
    output: "standalone",
    async headers() {
      return [
        ...(isDev
          ? []
          : [
              {
                source: "/_next/static/:path*",
                headers: [{ key: "Cache-Control", value: "public, max-age=31536000, immutable" }],
              },
            ]),
        { source: "/", headers: noStore },
        { source: "/platform", headers: noStore },
        { source: "/enterprise", headers: noStore },
        { source: "/product/:path*", headers: noStore },
        {
          source: "/sw.js",
          headers: [
            { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
            { key: "Service-Worker-Allowed", value: "/" },
          ],
        },
      ];
    },
  };
}
