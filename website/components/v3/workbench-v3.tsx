"use client";

import { Background, Controls, MiniMap, ReactFlow, addEdge, useEdgesState, useNodesState, type Connection, type Edge, type Node } from "@xyflow/react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, Check, CircleStop, Database, FileSearch, GitBranch, Play, ShieldCheck, UserCheck, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

const baseNodes: Node[] = [
  { id: "brief", position: { x: 40, y: 180 }, data: { label: "Business brief" }, type: "input", className: "flow-node brief" },
  { id: "analyst", position: { x: 260, y: 180 }, data: { label: "Business Analyst" }, className: "flow-node analyst" },
  { id: "compliance", position: { x: 520, y: 70 }, data: { label: "Compliance" }, className: "flow-node worker" },
  { id: "finance", position: { x: 520, y: 290 }, data: { label: "Finance" }, className: "flow-node worker" },
  { id: "approval", position: { x: 790, y: 180 }, data: { label: "Human approval" }, className: "flow-node approval" },
  { id: "erp", position: { x: 1040, y: 180 }, data: { label: "Create in ERP" }, type: "output", className: "flow-node system" },
];

const baseEdges: Edge[] = [
  { id: "e1", source: "brief", target: "analyst", animated: true },
  { id: "e2", source: "analyst", target: "compliance", animated: true },
  { id: "e3", source: "analyst", target: "finance", animated: true },
  { id: "e4", source: "compliance", target: "approval", animated: true },
  { id: "e5", source: "finance", target: "approval", animated: true },
  { id: "e6", source: "approval", target: "erp", animated: true },
];

const detail: Record<string, { title: string; type: string; description: string; icon: typeof Bot; tags: string[] }> = {
  brief: { title: "Business brief", type: "INPUT", description: "Natural-language objective supplied by an operator.", icon: WandSparkles, tags: ["Natural language", "Objective"] },
  analyst: { title: "Business Analyst", type: "INTELLIGENCE", description: "Decomposes intent into tasks, roles, systems, and checkpoints.", icon: FileSearch, tags: ["Memory", "Planning", "Reasoning"] },
  compliance: { title: "Compliance Specialist", type: "DIGITAL EMPLOYEE", description: "Checks sanctions, policy requirements, and missing evidence.", icon: ShieldCheck, tags: ["Policies", "Vendor data"] },
  finance: { title: "Finance Specialist", type: "DIGITAL EMPLOYEE", description: "Calculates financial risk and routes material exceptions.", icon: Bot, tags: ["Risk model", "Finance"] },
  approval: { title: "Human approval", type: "CONTROL", description: "High-impact ERP actions wait for a human decision.", icon: UserCheck, tags: ["HITL", "Approval"] },
  erp: { title: "Create in ERP", type: "SYSTEM ACTION", description: "Writes the approved supplier into the enterprise system.", icon: Database, tags: ["ERP", "Write action"] },
};

const order = ["brief", "analyst", "compliance", "finance", "approval", "erp"];

export function WorkbenchV3() {
  const [nodes, setNodes, onNodesChange] = useNodesState(baseNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(baseEdges);
  const [selected, setSelected] = useState("analyst");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState<string[]>([]);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const activeDetail = detail[selected];
  const Icon = activeDetail.icon;

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const decoratedNodes = useMemo(() => nodes.map(node => ({
    ...node,
    className: `${node.className || ""} ${done.includes(node.id) ? "flow-complete" : ""}`,
  })), [nodes, done]);

  function onConnect(connection: Connection) {
    setEdges(eds => addEdge({ ...connection, animated: true }, eds));
  }

  function stop() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setRunning(false);
  }

  function run() {
    stop();
    setDone([]);
    setRunning(true);
    order.forEach((id, i) => {
      const t = setTimeout(() => {
        setDone(prev => [...prev, id]);
        setSelected(id);
        if (i === order.length - 1) setRunning(false);
      }, 620 * (i + 1));
      timers.current.push(t);
    });
  }

  return (
    <section className="v3-workbench">
      <div className="v3-section-label"><span>03 / WORKFLOW RUNTIME</span><p>Not a diagram. A live execution surface.</p></div>
      <div className="v3-workbench-heading"><h2>Compose work like a system.<br/><span>Run it like one.</span></h2><p>The same runtime coordinates AI workers, humans, tools, state, and enterprise actions. Drag the graph, inspect nodes, then run the workflow.</p></div>

      <div className="v3-workbench-shell">
        <div className="v3-workbench-topbar">
          <div className="v3-window-dots"><i/><i/><i/></div>
          <div className="v3-workbench-tabs"><span className="active">vendor-onboarding.flow</span><span>policies</span><span>run history</span></div>
          <div className="v3-run-actions"><button onClick={run} disabled={running}><Play size={13}/>{running ? "Running" : "Run workflow"}</button>{running && <button className="stop" onClick={stop}><CircleStop size={13}/> Stop</button>}</div>
        </div>

        <div className="v3-workbench-body">
          <aside className="v3-flow-library">
            <span>BLOCKS</span>
            <button><WandSparkles size={15}/><b>Intent</b></button>
            <button><Bot size={15}/><b>Digital worker</b></button>
            <button><GitBranch size={15}/><b>Branch</b></button>
            <button><UserCheck size={15}/><b>Human gate</b></button>
            <button><Database size={15}/><b>System action</b></button>
            <div className="v3-library-status"><i/><div><b>Execution fabric</b><small>All systems healthy</small></div></div>
          </aside>

          <div className="v3-flow-canvas">
            <ReactFlow
              nodes={decoratedNodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => setSelected(node.id)}
              fitView
              fitViewOptions={{ padding: .16, duration: 520 }}
              minZoom={.25}
              maxZoom={1.7}
              onlyRenderVisibleElements
            >
              <Background gap={26} size={1} />
              <MiniMap pannable zoomable />
              <Controls showInteractive={false} />
            </ReactFlow>
            <AnimatePresence>
              {running && <motion.div className="v3-run-toast" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}><i/><span>Execution in progress</span><b>{done.length}/{order.length}</b></motion.div>}
              {!running && done.length === order.length && <motion.div className="v3-run-toast success" initial={{ opacity:0 }} animate={{ opacity:1 }}><Check size={14}/><span>Workflow completed</span><b>3.7s</b></motion.div>}
            </AnimatePresence>
          </div>

          <aside className="v3-node-inspector">
            <span>INSPECTOR</span>
            <div className="v3-inspector-icon"><Icon size={18}/></div>
            <small>{activeDetail.type}</small>
            <h3>{activeDetail.title}</h3>
            <p>{activeDetail.description}</p>
            <div className="v3-inspector-tags">{activeDetail.tags.map(tag => <b key={tag}>{tag}</b>)}</div>
            <div className="v3-inspector-rule"><span>Autonomy</span><b>{selected === "approval" ? "Human" : selected === "erp" ? "Controlled" : "Auto"}</b></div>
            <div className="v3-inspector-rule"><span>Audit</span><b>Enabled</b></div>
            <div className="v3-inspector-rule"><span>Run state</span><b>{done.includes(selected) ? "Complete" : running ? "Queued" : "Ready"}</b></div>
          </aside>
        </div>
        <div className="v3-workbench-console"><span>$ aegis run vendor-onboarding</span><b>{running ? `executing node ${Math.min(done.length + 1, order.length)} of ${order.length}...` : done.length === order.length ? "completed · outcome persisted · trace available" : "ready"}</b></div>
      </div>
    </section>
  );
}
