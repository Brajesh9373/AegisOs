import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

const linkColumns = [
  {
    title: "PRODUCT",
    links: [
      ["Platform", "/platform"],
      ["BA Agent", "/product/ba-agent"],
      ["Frappe Agent", "/product/frappe-agent"],
      ["Project Agent", "/product/project-agent"],
      ["Functional Agent", "/product/functional-agent"],
      ["Technical Agent", "/product/technical-agent"],
    ],
  },
] as const;

export function SiteFooterV3() {
  return (
    <footer className="v3-footer v9-footer">
      <div className="v9-footer-glow" aria-hidden="true" />

      <div className="v3-footer-top v9-footer-top">
        <Link href="/" className="v9-footer-wordmark" aria-label="Worksimplified home">Worksimplified</Link>

        <div className="v9-footer-cols">
          <nav className="v3-footer-links" aria-label="Footer navigation">
            {linkColumns.map(({ title, links }) => (
              <div key={title}>
                <span>{title}</span>
                {links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}
              </div>
            ))}
          </nav>

          <div className="v9-footer-note">
            <span>WHAT THIS IS</span>
            <p>Six specialist agents carry one business requirement to a running Frappe application — flow diagram, data model, API surface and workflow rules generated from the brief.</p>
            <a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={13} /></a>
          </div>
        </div>
      </div>

      <div className="v3-footer-bottom">
        <span>© 2026 Worksimplified. All rights reserved.</span>
        <span>Requirement in, running system out.</span>
        <span>Privacy · Terms · Security</span>
      </div>
    </footer>
  );
}
