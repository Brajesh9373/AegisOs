import Link from "next/link";

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
        <Link href="/" className="v9-footer-wordmark" aria-label="Worksimplified home">Worksimplified</Link>
        <nav className="v3-footer-links" aria-label="Footer navigation">
          {linkColumns.map(({ title, links }) => (
            <div key={title}>
              <span>{title}</span>
              {links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}
            </div>
          ))}
        </nav>
      </div>

      <div className="v3-footer-bottom"><span>© 2026 Worksimplified. All rights reserved.</span><span>Business intent → governed execution.</span><span>Privacy · Terms · Security</span></div>
    </footer>
  );
}
