"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, ChevronDown, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

const productColumns = [
  {
    title: "UNDERSTAND",
    items: [
      ["BA Agent", "/product/ba-agent", "Discuss the project and generate the flow diagram."],
    ],
  },
  {
    title: "DELIVER",
    items: [
      ["Frappe Agent", "/product/frappe-agent", "Connect the backend and go live in Frappe."],
      ["Project Agent", "/product/project-agent", "Track scope, milestones, and deliverables."],
    ],
  },
  {
    title: "BUILD",
    items: [
      ["Functional Agent", "/product/functional-agent", "Map functionalities and user actions."],
      ["Technical Agent", "/product/technical-agent", "Design schemas, APIs, and architecture."],
    ],
  },
];

export function SiteHeaderV3() {
  const [open, setOpen] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 30);
      if (window.scrollY > 100) setOpen(false);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`v3-header ${scrolled ? "is-scrolled" : ""}`}>
      <div className="v3-nav-shell">
        <Link href="/" className="v3-brand" aria-label="Worksimplified home">
          <span className="v3-brand-glyph"><i /><i /><i /></span>
          <strong>Worksimplified</strong>
        </Link>

        <nav className="v3-nav" aria-label="Primary navigation">
          <div className="v3-product-nav" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
            <button onClick={() => setOpen(v => !v)} aria-expanded={open}>
              Product <ChevronDown size={13} />
            </button>
            <AnimatePresence>
              {open && (
                <motion.div
                  className="v3-mega"
                  initial={{ opacity: 0, y: -7, scale: .992 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -5, scale: .995 }}
                  transition={{ type: "spring", stiffness: 340, damping: 31, mass: .55 }}
                >
                  <div className="v3-mega-feature">
                    <span>THE AGENT PIPELINE</span>
                    <h3>Six specialist agents, from requirement to running system.</h3>
                    <p>Discuss the project, refine the output, connect the backend, and carry it through functional and technical design.</p>
                    <Link href="/platform" onClick={() => setOpen(false)}>Platform overview <ArrowUpRight size={14} /></Link>
                    <div className="v3-mini-runtime" aria-hidden="true">
                      <div>Discover</div><i /><div>Refine</div><i /><div>Connect</div><i /><div>Build</div>
                    </div>
                  </div>
                  <div className="v3-mega-columns">
                    {productColumns.map(column => (
                      <div key={column.title}>
                        <span>{column.title}</span>
                        {column.items.map(([label, href, text]) => (
                          <Link key={href} href={href} onClick={() => setOpen(false)}>
                            <b>{label}</b><small>{text}</small>
                          </Link>
                        ))}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <Link href="/platform">Platform</Link>
          <Link href="/enterprise">Enterprise</Link>
          <a href="#architecture">How it works</a>
        </nav>

        <div className="v3-nav-actions">
          <a href="/login" className="v3-text-button">Sign in</a>
          <a href="/login" className="v3-solid-button">Get started <ArrowUpRight size={14} /></a>
        </div>

        <button className="v3-mobile-toggle" onClick={() => setMobile(v => !v)} aria-label="Toggle navigation">
          {mobile ? <X /> : <Menu />}
        </button>
      </div>

      <AnimatePresence>
        {mobile && (
          <motion.div className="v3-mobile-menu" initial={{ opacity: 0, y: -10, scale: .99 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -8, scale: .99 }} transition={{ type: "spring", stiffness: 320, damping: 30 }}>
            <Link href="/platform" onClick={() => setMobile(false)}>Platform</Link>
            {productColumns.flatMap(c => c.items).map(([label, href]) => <Link href={href} key={href} onClick={() => setMobile(false)}>{label}</Link>)}
            <Link href="/enterprise" onClick={() => setMobile(false)}>Enterprise</Link>
            <a href="/login" className="v3-solid-button" onClick={() => setMobile(false)}>Get started</a>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
