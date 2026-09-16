import type { Metadata } from "next";
import "lenis/dist/lenis.css";
import "./globals.css";
import "./light-theme.css";
import "./perfection.css";
import "./system-cards-v8.css";
import "./v9-polish.css";
import "./workforce-v10.css";
import "./intro-v11.css";
import "./agent-pipeline.css";
import "./platform-panels.css";
import { SiteHeaderV3 } from "@/components/v3/site-header-v3";
import { SiteFooterV3 } from "@/components/v3/site-footer-v3";
import { ExperienceRuntimeV4 } from "@/components/v3/experience-runtime-v4";
import { SmoothScrollRuntimeV11 } from "@/components/v3/smooth-scroll-runtime-v11";

export const metadata: Metadata = {
  title: {
    default: "Worksimplified — From idea to code, through specialist agents.",
    template: "%s | Worksimplified",
  },
  description:
    "Worksimplified is an agent-driven development platform. Discuss your project with the BA Agent, iterate through the refinement loop, connect Frappe, and get production code.",
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
