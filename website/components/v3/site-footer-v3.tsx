import Link from "next/link";

const linkColumns = [
  {
    title: "PRODUCT",
    links: [
      ["Platform", "/platform"],
      ["Business Analyst", "/product/business-analyst"],
      ["AI Workforce", "/product/workforce"],
      ["Workflow Engine", "/product/workflows"],
      ["Governance", "/product/governance"],
    ],
  },
  {
    title: "COMPANY",
    links: [
      ["Enterprise", "/enterprise"],
      ["Contact", "/#contact"],
      ["How it works", "/#architecture"],
      ["Security", "/#"],
    ],
  },
  {
    title: "RESOURCES",
    links: [
      ["Documentation", "/#"],
      ["Architecture", "/#"],
      ["Changelog", "/#"],
      ["Trust center", "/#"],
    ],
  },
] as const;

export function SiteFooterV3() {
  return (
    <footer className="v3-footer v9-footer" id="resources">
      <div className="v9-footer-glow" aria-hidden="true" />

      <div className="v3-footer-top v9-footer-top">
        <Link href="/" className="v9-footer-wordmark" aria-label="AegisOS home">AegisOS</Link>
        <nav className="v3-footer-links" aria-label="Footer navigation">
          {linkColumns.map(({ title, links }) => (
            <div key={title}>
              <span>{title}</span>
              {links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}
            </div>
          ))}
        </nav>
      </div>

      <div className="v3-footer-bottom"><span>© 2026 AegisOS. All rights reserved.</span><span>Business intent → governed execution.</span><span>Privacy · Terms · Security</span></div>
    </footer>
  );
}
