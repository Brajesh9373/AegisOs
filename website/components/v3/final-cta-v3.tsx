"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export function FinalCtaV3() {
  return (
    <section className="v3-final" id="contact">
      <div className="v3-final-orbit orbit-one"/><div className="v3-final-orbit orbit-two"/><div className="v3-final-orbit orbit-three"/>
      <motion.div className="v3-final-core" initial={{opacity:0}} whileInView={{opacity:1}} viewport={{once:true,amount:.4}} transition={{duration:.8,ease:[.16,1,.3,1]}}><span className="v3-brand-glyph"><i/><i/><i/></span></motion.div>
      <div className="v3-final-copy"><span>THE OPERATING LAYER FOR AI WORK</span><h2>Bring the business problem.<br/><em>AegisOS handles what happens next.</em></h2><p>Move from isolated assistants to one governed system for understanding, coordinating, executing, and operating AI across the organization.</p><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={16}/></a></div>
    </section>
  );
}
