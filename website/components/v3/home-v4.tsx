"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { HeroV3 } from "./hero-v3";
import { BrandZoomIntroV11 } from "./brand-zoom-intro-v11";
import { ManifestoV3 } from "./manifesto-v3";

const PlatformSystemV8 = dynamic(() => import("./platform-system-v8").then(m => m.PlatformSystemV8), { ssr: false });
const WorkbenchV3 = dynamic(() => import("./workbench-v3").then(m => m.WorkbenchV3), { ssr: false });
const ProductBentoV3 = dynamic(() => import("./product-bento-v3").then(m => m.ProductBentoV3), { ssr: false });
const IntegrationFieldV3 = dynamic(() => import("./integration-field-v3").then(m => m.IntegrationFieldV3), { ssr: false });
const OperationsV3 = dynamic(() => import("./operations-v3").then(m => m.OperationsV3), { ssr: false });
const FinalCtaV3 = dynamic(() => import("./final-cta-v3").then(m => m.FinalCtaV3), { ssr: false });

function DeferredMount({ children, minHeight = 760, rootMargin = "900px" }: { children: ReactNode; minHeight?: number; rootMargin?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (ready || !ref.current) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setReady(true);
        observer.disconnect();
      }
    }, { rootMargin });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ready, rootMargin]);

  return <div ref={ref} style={!ready ? { minHeight } : undefined}>{ready ? children : <div className="v4-section-skeleton" aria-hidden="true" />}</div>;
}

export function HomeV4() {
  return (
    <>
      <BrandZoomIntroV11 />
      <HeroV3 />
      <ManifestoV3 />
      <DeferredMount minHeight={900}><PlatformSystemV8 /></DeferredMount>
      <DeferredMount minHeight={900}><WorkbenchV3 /></DeferredMount>
      <DeferredMount minHeight={820}><ProductBentoV3 /></DeferredMount>
      <DeferredMount minHeight={820}><IntegrationFieldV3 /></DeferredMount>
      <DeferredMount minHeight={900}><OperationsV3 /></DeferredMount>
      <DeferredMount minHeight={760}><FinalCtaV3 /></DeferredMount>
    </>
  );
}
