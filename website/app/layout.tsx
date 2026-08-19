import type { Metadata } from "next";
import "@xyflow/react/dist/style.css";
import "lenis/dist/lenis.css";
import "./globals.css";
import "./light-theme.css";
import "./perfection.css";
import "./system-cards-v8.css";
import "./v9-polish.css";
import "./workforce-v10.css";
import "./intro-v11.css";
import { SiteHeaderV3 } from "@/components/v3/site-header-v3";
import { SiteFooterV3 } from "@/components/v3/site-footer-v3";
import { ExperienceRuntimeV4 } from "@/components/v3/experience-runtime-v4";
import { SmoothScrollRuntimeV11 } from "@/components/v3/smooth-scroll-runtime-v11";

export const metadata: Metadata = {
  title: {
    default: "AegisOS — Business intent, executed.",
    template: "%s | AegisOS",
  },
  description:
    "AegisOS is an enterprise AI operating system that turns business intent into governed execution across people, AI workers, and enterprise systems.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <SmoothScrollRuntimeV11 />
        <ExperienceRuntimeV4 />
        <SiteHeaderV3 />
        <main>{children}</main>
        <SiteFooterV3 />
      </body>
    </html>
  );
}
