"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { HeroV3 } from "./hero-v3";
import { BrandZoomIntroV11 } from "./brand-zoom-intro-v11";
import { AgentBentoV3 } from "./agent-bento-v3";
import { PlatformSystemV8 } from "./platform-system-v8";
import { FinalCtaV3 } from "./final-cta-v3";

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
      <DeferredMount minHeight={900}><PlatformSystemV8 /></DeferredMount>
      <DeferredMount minHeight={820}><AgentBentoV3 /></DeferredMount>
      <DeferredMount minHeight={760}><FinalCtaV3 /></DeferredMount>
    </>
  );
}
