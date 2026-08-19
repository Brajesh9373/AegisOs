"use client";

import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, ArrowDownRight, ArrowUpRight, CircleCheck, CircleDollarSign, Clock3, Eye, ShieldCheck, Users } from "lucide-react";

const datasets = {
  Runs: [31,42,38,57,49,65,72,69,82,78,91,96],
  Success: [91,93,92,94,94,95,96,95,97,97,98,98],
  Cost: [82,78,75,72,70,66,64,61,58,57,54,51],
};

export function OperationsV3() {
  const [metric, setMetric] = useState<keyof typeof datasets>("Runs");
  const data = useMemo(()=>datasets[metric].map((value,i)=>({name:`${i+8}:00`,value})),[metric]);
  return (
    <section className="v3-operations">
      <div className="v3-section-label"><span>06 / CONTROL CENTER</span><p>Operate AI with the visibility expected from production infrastructure.</p></div>
      <div className="v3-operations-heading"><h2>Know what your AI organization<br/><span>is doing right now.</span></h2><p>Runs, workforce activity, human reviews, reliability, spend, and business outcomes in one operational surface.</p></div>
      <div className="v3-console-shell">
        <div className="v3-console-sidebar">
          <div className="v3-console-brand"><span className="v3-brand-glyph"><i/><i/><i/></span><b>Control Center</b></div>
          {[["Overview",Activity],["Workforce",Users],["Workflows",Eye],["Runs",Clock3],["Approvals",ShieldCheck],["Costs",CircleDollarSign],["Governance",ShieldCheck]].map(([x,Icon],i)=>{ const NavIcon = Icon as typeof Activity; return <button className={i===0?"active":""} key={String(x)}><NavIcon size={14}/><span>{String(x)}</span>{x==="Approvals"&&<em>4</em>}</button>})}
          <div className="v3-console-org"><i/><div><b>Production</b><small>All systems healthy</small></div></div>
        </div>
        <div className="v3-console-main">
          <div className="v3-console-top"><div><span>ORGANIZATION / PRODUCTION</span><h3>Execution overview</h3></div><div><span className="live"><i/> LIVE</span><button>Last 24 hours⌄</button></div></div>
          <div className="v3-kpis">
            <div><span>RUNS TODAY</span><b>846</b><small className="up"><ArrowUpRight/>18.4%</small></div>
            <div><span>SUCCESS RATE</span><b>97.8%</b><small className="up"><ArrowUpRight/>1.4%</small></div>
            <div><span>HUMAN REVIEWS</span><b>13</b><small className="down"><ArrowDownRight/>8.1%</small></div>
            <div><span>AI SPEND</span><b>$1,284</b><small className="down"><ArrowDownRight/>7.8%</small></div>
          </div>
          <div className="v3-console-grid">
            <div className="v3-chart-card">
              <div className="v3-chart-head"><div><span>EXECUTION TELEMETRY</span><b>{metric}</b></div><div>{Object.keys(datasets).map(x=><button className={metric===x?"active":""} key={x} onClick={()=>setMetric(x as keyof typeof datasets)}>{x}</button>)}</div></div>
              <div className="v3-chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{top:10,right:5,left:-28,bottom:0}}><defs><linearGradient id="aegisArea" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3157d5" stopOpacity={.32}/><stop offset="95%" stopColor="#3157d5" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(89,111,145,.12)"/><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill:"#8290a5",fontSize:10}}/><YAxis axisLine={false} tickLine={false} tick={{fill:"#8290a5",fontSize:10}}/><Tooltip contentStyle={{background:"#ffffff",color:"#0c1830",border:"1px solid #d9e2ed",borderRadius:10,fontSize:12,boxShadow:"0 14px 36px rgba(28,48,82,.12)"}}/><Area type="monotone" dataKey="value" stroke="#3157d5" fill="url(#aegisArea)" strokeWidth={2.2}/></AreaChart></ResponsiveContainer></div>
            </div>
            <div className="v3-runs-card"><div className="v3-runs-head"><span>RECENT RUNS</span><button>View all ↗</button></div>{[
              ["Vendor onboarding","Completed","3.7s","$0.42"],["Invoice exception","Human review","1m 12s","$0.18"],["Renewal analysis","Completed","9.4s","$0.31"],["Customer escalation","Completed","6.1s","$0.27"]
            ].map(([name,state,time,cost],i)=><motion.div className="v3-run-row" key={name} initial={{opacity:0,x:10}} whileInView={{opacity:1,x:0}} transition={{delay:i*.05}} viewport={{once:true}}><span className={state==="Human review"?"review":"ok"}>{state==="Human review"?<ShieldCheck size={13}/>:<CircleCheck size={13}/>}</span><div><b>{name}</b><small>Run #{2841-i}</small></div><em>{state}</em><small>{time}</small><strong>{cost}</strong></motion.div>)}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
