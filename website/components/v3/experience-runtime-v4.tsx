"use client";

import { motion, useScroll, useSpring } from "framer-motion";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const warmRoutes = [
  "/platform",
  "/enterprise",
  "/product/business-analyst",
  "/product/workflows",
  "/product/governance",
];

export function ExperienceRuntimeV4() {
  const router = useRouter();
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 115, damping: 28, mass: .24 });

  useEffect(() => {
    const warm = () => warmRoutes.forEach(route => router.prefetch(route));
    const win = window as Window & {
      requestIdleCallback?: (cb: () => void, opts?: { timeout: number }) => number;
      cancelIdleCallback?: (id: number) => void;
    };
    const idleId = win.requestIdleCallback
      ? win.requestIdleCallback(warm, { timeout: 1800 })
      : window.setTimeout(warm, 700);

    // V8 deliberately removes the previous page-level service-worker cache.
    // Next's hashed static assets remain immutable-cached, while navigation stays fresh.
    // This prevents older UI bundles from surviving a redesign and appearing after deploys.
    const clearLegacyAegisCaches = async () => {
      if ("serviceWorker" in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registrations.map(registration => registration.unregister()));
      }
      if ("caches" in window) {
        const keys = await caches.keys();
        await Promise.all(keys.filter(key => key.startsWith("aegisos-")).map(key => caches.delete(key)));
      }
    };

    clearLegacyAegisCaches().catch(() => undefined);

    return () => {
      if (win.cancelIdleCallback && typeof idleId === "number") win.cancelIdleCallback(idleId);
      else window.clearTimeout(idleId);
    };
  }, [router]);

  return (
    <div className="v4-scroll-progress" aria-hidden="true">
      <motion.i style={{ scaleX }} />
    </div>
  );
}
