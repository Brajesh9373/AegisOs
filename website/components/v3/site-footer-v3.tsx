import Link from "next/link";
import { ArrowUpRight, CheckCircle2 } from "lucide-react";

export function SiteFooterV3() {
  return (
    <footer className="v3-footer v9-footer" id="resources">
      <div className="v9-footer-glow" aria-hidden="true" />
      <div className="v9-footer-cta">
        <div><span>READY FOR PRODUCTION AI</span><h2>Turn business intent into<br/>governed execution.</h2></div>
        <div className="v9-footer-cta-side"><p>See how AegisOS can coordinate AI workers, enterprise systems, policies and humans as one operating layer.</p><div><a className="v9-footer-primary" href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a><Link href="/platform">Explore platform</Link></div></div>
      </div>

      <div className="v3-footer-top v9-footer-top">
        <div className="v9-footer-brand-block">
          <div className="v3-footer-brand"><span className="v3-brand-glyph"><i /><i /><i /></span><strong>AegisOS</strong></div>
          <p>The enterprise operating system for governed AI execution.</p>
          <div className="v9-footer-status"><CheckCircle2 size={13}/><span>Platform operational</span><small>Enterprise runtime</small></div>
        </div>
        <div className="v3-footer-links">
          <div><span>PRODUCT</span><Link href="/platform">Platform</Link><Link href="/product/business-analyst">Business Analyst</Link><Link href="/product/workforce">AI Workforce</Link><Link href="/product/workflows">Workflow Engine</Link><Link href="/product/governance">Governance</Link></div>
          <div><span>COMPANY</span><Link href="/enterprise">Enterprise</Link><a href="#contact">Contact</a><a href="#architecture">How it works</a><a href="#">Security</a></div>
          <div><span>RESOURCES</span><a href="#">Documentation</a><a href="#">Architecture</a><a href="#">Changelog</a><a href="#">Trust center</a></div>
        </div>
      </div>

      <div className="v9-footer-wordmark" aria-hidden="true">AegisOS</div>
      <div className="v3-footer-bottom"><span>© 2026 AegisOS. All rights reserved.</span><span>Business intent → governed execution.</span><span>Privacy · Terms · Security</span></div>
    </footer>
  );
}
