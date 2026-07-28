const output = document.querySelector("#output");
const apiKeyInput = document.querySelector("#apiKey");

const jsonHeaders = () => {
  const headers = { "Content-Type": "application/json" };
  const apiKey = apiKeyInput.value.trim();
  if (apiKey) headers["X-API-Key"] = apiKey;
  return headers;
};

const writeOutput = (title, data) => {
  const payload = {
    at: new Date().toISOString(),
    title,
    data,
  };
  output.textContent = JSON.stringify(payload, null, 2);
};

const requestJson = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...jsonHeaders(),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }
  if (!response.ok) {
    throw new Error(JSON.stringify({ status: response.status, body }, null, 2));
  }
  return body;
};

const formPayload = (form) => {
  const data = new FormData(form);
  const payload = {};
  for (const [key, value] of data.entries()) {
    const field = form.elements[key];
    if (field?.type === "checkbox") {
      payload[key] = field.checked;
    } else if (field?.type === "number") {
      payload[key] = Number(value);
    } else if (value !== "") {
      payload[key] = value;
    }
  }
  for (const checkbox of form.querySelectorAll('input[type="checkbox"]')) {
    payload[checkbox.name] = checkbox.checked;
  }
  return payload;
};

const handleSubmit = (selector, handler) => {
  const form = document.querySelector(selector);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const original = button.textContent;
    button.disabled = true;
    button.textContent = "Working...";
    try {
      const result = await handler(formPayload(form));
      writeOutput(form.id, result);
    } catch (error) {
      writeOutput(`${form.id} failed`, error.message);
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  });
};

const setDot = (dot, label, ok, text) => {
  dot.classList.remove("ok", "error", "pending");
  dot.classList.add(ok ? "ok" : "error");
  label.textContent = text;
};

const refreshHealth = async () => {
  const serviceDot = document.querySelector("#serviceStatus");
  const serviceLabel = document.querySelector("#serviceLabel");
  const graphDot = document.querySelector("#graphStatus");
  const graphLabel = document.querySelector("#graphLabel");

  try {
    const service = await requestJson("/health", { headers: {} });
    setDot(serviceDot, serviceLabel, service.status === "ok", `${service.service} ${service.version}`);
  } catch (error) {
    setDot(serviceDot, serviceLabel, false, "Service error");
  }

  try {
    const graph = await requestJson("/health/graph", { headers: {} });
    setDot(graphDot, graphLabel, graph.status === "ok", graph.status === "ok" ? graph.graph : "Graph error");
    if (graph.status !== "ok") writeOutput("graph health", graph);
  } catch (error) {
    setDot(graphDot, graphLabel, false, "Graph error");
  }
};

const loadProviders = async () => {
  const providers = await requestJson("/providers", { headers: {} });
  const grid = document.querySelector("#providerGrid");
  grid.innerHTML = providers
    .map(
      (provider) => `
        <article class="provider-card">
          <p class="eyebrow">${provider.version}</p>
          <h3>${provider.name}</h3>
          <div class="chips">
            ${provider.capabilities.map((capability) => `<span class="chip">${capability}</span>`).join("")}
          </div>
        </article>
      `,
    )
    .join("");
  writeOutput("providers", providers);
};

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.target}`).classList.add("active");
  });
});

document.querySelector("#refreshHealth").addEventListener("click", refreshHealth);
document.querySelector("#loadProviders").addEventListener("click", loadProviders);
document.querySelector("#clearOutput").addEventListener("click", () => {
  output.textContent = "{ \"cleared\": true }";
});

handleSubmit("#gitForm", (payload) =>
  requestJson("/providers/git/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
);

handleSubmit("#mysqlForm", (payload) =>
  requestJson("/providers/mysql/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
);

handleSubmit("#ukoForm", (payload) => {
  const now = new Date().toISOString();
  return requestJson("/ingest/uko", {
    method: "POST",
    body: JSON.stringify({
      persist: payload.persist,
      uko: {
        type: payload.type,
        name: payload.name,
        content: payload.content,
        metadata: {
          source: payload.source,
          source_id: payload.source_id,
          created_at: now,
          modified_at: now,
          tags: ["manual-ui"],
        },
      },
    }),
  });
});

handleSubmit("#memoryForm", (payload) =>
  requestJson("/memory/notes", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
);

handleSubmit("#memorySearchForm", (payload) =>
  requestJson(`/memory/notes?q=${encodeURIComponent(payload.q || "")}`, {
    method: "GET",
    headers: {},
  }),
);

handleSubmit("#queryForm", (payload) =>
  requestJson("/query", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
);

let graphSimulation = null;

const colorScale = d3.scaleOrdinal()
  .domain(["episode", "file", "document", "function", "class", "table", "column", "import", "person", "concept", "api"])
  .range(["#c6532c", "#2f6f9f", "#1f8f5f", "#8b5cf6", "#e07b3c", "#3cb44b", "#e066a3", "#ffb347"]);

document.querySelector("#loadGraph").addEventListener("click", async () => {
  const container = document.querySelector("#graphContainer");
  const stats = document.querySelector("#graphStats");
  const button = document.querySelector("#loadGraph");

  button.disabled = true;
  button.textContent = "Loading...";
  try {
    const filter = document.querySelector("#graphSearch").value.trim();
    const query = new URLSearchParams({ limit: "700" });
    if (filter) query.set("q", filter);
    const data = await requestJson(`/graph/data?${query.toString()}`);
    if (!data.nodes || data.nodes.length === 0) {
      stats.textContent = "Graph is empty - sync data first with persist enabled";
      container.innerHTML = '<div class="graph-empty">No graph data yet. Check "Persist" when syncing.</div>';
      return;
    }
    stats.textContent = `${data.node_count} nodes, ${data.edge_count} edges`;
    renderGraph(data, container);
  } catch (error) {
    stats.textContent = "Failed to load graph data";
    writeOutput("graph load failed", error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Refresh graph";
  }
});

function renderGraph(data, container) {
  container.innerHTML = "";
  const width = container.clientWidth || 700;
  const height = 560;

  const svg = d3.select(container)
    .append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto; background: #0a0d0c; border-radius: 8px;");

  const zoom = d3.zoom()
    .scaleExtent([0.15, 4])
    .on("zoom", (event) => g.attr("transform", event.transform));
  svg.call(zoom);

  const g = svg.append("g");

  const nodes = data.nodes.map(n => ({ ...n }));
  const edges = data.edges.map(e => ({
    ...e,
    source: e.from_,
    target: e.to,
  }));

  const lookup = new Map(nodes.map(n => [n.id, n]));
  const validEdges = edges.filter(e => lookup.has(e.source) && lookup.has(e.target));
  const groupedSources = () => {
    const groups = new Map();
    for (const n of nodes) {
      if (!n.source_group) continue;
      if (!groups.has(n.source_group)) groups.set(n.source_group, []);
      groups.get(n.source_group).push(n);
    }
    return [...groups.entries()]
      .filter(([, members]) => members.length > 1)
      .map(([id, members]) => ({ id, members }));
  };

  const sourceLayer = g.append("g").attr("class", "source-boundaries");
  const sourceBoundary = sourceLayer
    .selectAll("g")
    .data(groupedSources(), d => d.id)
    .join("g")
    .attr("class", "source-boundary");

  sourceBoundary.append("ellipse")
    .attr("fill", "rgba(198, 83, 44, 0.08)")
    .attr("stroke", "rgba(255, 157, 119, 0.55)")
    .attr("stroke-width", 1.4)
    .attr("stroke-dasharray", "8 7");

  sourceBoundary.append("text")
    .attr("fill", "#ffcfbd")
    .attr("font-size", 11)
    .attr("font-weight", 700)
    .attr("pointer-events", "none")
    .text(d => d.id.length > 42 ? d.id.slice(0, 40) + "..." : d.id);

  const link = g.append("g")
    .selectAll("line")
    .data(validEdges)
    .join("line")
    .attr("stroke", "#334438")
    .attr("stroke-width", 1.2)
    .attr("stroke-opacity", 0.55);

  const node = g.append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .call(d3.drag()
      .on("start", (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
    );

  const radiusScale = d3.scaleLinear()
    .domain([1, Math.max(10, nodes.length / 2)])
    .range([8, 28]);

  node.append("circle")
    .attr("r", d => radiusScale(Math.max(1, edges.filter(e => e.source === d.id || e.target === d.id).length)))
    .attr("fill", d => colorScale(d.group))
    .attr("stroke", "#1a1f1c")
    .attr("stroke-width", 1.5);

  node.append("text")
    .text(d => d.label.length > 32 ? d.label.slice(0, 30) + "..." : d.label)
    .attr("font-size", 10)
    .attr("fill", "#d9ffe8")
    .attr("dx", d => radiusScale(Math.max(1, edges.filter(e => e.source === d.id || e.target === d.id).length)) + 6)
    .attr("dy", 4)
    .attr("pointer-events", "none");

  node.append("title")
    .text(d => d.title || d.label);

  const sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(validEdges).id(d => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-350))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(35))
    .force("sourceCluster", sourceClusterForce(nodes))
    .on("tick", () => {
      sourceBoundary.each(function(d) {
        const xs = d.members.map(n => n.x || 0);
        const ys = d.members.map(n => n.y || 0);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        const rx = Math.max(70, (maxX - minX) / 2 + 48);
        const ry = Math.max(54, (maxY - minY) / 2 + 42);
        d3.select(this).select("ellipse")
          .attr("cx", cx)
          .attr("cy", cy)
          .attr("rx", rx)
          .attr("ry", ry);
        d3.select(this).select("text")
          .attr("x", cx - rx + 16)
          .attr("y", cy - ry + 22);
      });

      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

  graphSimulation = sim;

  const pauseCheckbox = document.querySelector("#graphPause");
  pauseCheckbox.onchange = () => {
    if (pauseCheckbox.checked) {
      sim.stop();
    } else {
      sim.alpha(0.3).restart();
    }
  };
}

function sourceClusterForce(nodes) {
  let strength = 0.025;
  function force(alpha) {
    const groups = new Map();
    for (const node of nodes) {
      if (!node.source_group) continue;
      if (!groups.has(node.source_group)) groups.set(node.source_group, { x: 0, y: 0, count: 0 });
      const group = groups.get(node.source_group);
      group.x += node.x || 0;
      group.y += node.y || 0;
      group.count += 1;
    }
    for (const group of groups.values()) {
      group.x /= group.count || 1;
      group.y /= group.count || 1;
    }
    for (const node of nodes) {
      const group = groups.get(node.source_group);
      if (!group || group.count < 2) continue;
      node.vx += (group.x - node.x) * strength * alpha;
      node.vy += (group.y - node.y) * strength * alpha;
    }
  }
  force.strength = value => {
    if (!arguments.length) return strength;
    strength = value;
    return force;
  };
  return force;
}

refreshHealth();
loadProviders();
