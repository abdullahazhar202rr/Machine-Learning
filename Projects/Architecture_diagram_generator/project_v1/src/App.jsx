import React, { useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import ELK from "elkjs/lib/elk.bundled.js";

const elk = new ELK();

const TIER_STYLES = {
  frontend: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    border: "#667eea",
    shadow: "0 12px 32px rgba(102, 126, 234, 0.35)",
    color: "#ffffff",
  },
  api: {
    background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    border: "#f093fb",
    shadow: "0 12px 32px rgba(240, 147, 251, 0.35)",
    color: "#ffffff",
  },
  core: {
    background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    border: "#4facfe",
    shadow: "0 12px 32px rgba(79, 172, 254, 0.35)",
    color: "#ffffff",
  },
  data: {
    background: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    border: "#43e97b",
    shadow: "0 12px 32px rgba(67, 233, 123, 0.35)",
    color: "#ffffff",
  },
  external: {
    background: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    border: "#fa709a",
    shadow: "0 12px 32px rgba(250, 112, 154, 0.35)",
    color: "#ffffff",
  },
};

const ICONS = {
  cdn: "🌐",
  mobile: "📱",
  web: "🖥️",
  frontend: "🌐",
  api: "🔌",
  gateway: "🔌",
  "load balancer": "⚖️",
  auth: "🔒",
  service: "⚙️",
  server: "🖥️",
  database: "🗄️",
  postgres: "🗄️",
  redis: "⚡",
  cache: "⚡",
  kafka: "📨",
  queue: "📨",
  payment: "💳",
  notification: "🔔",
  external: "☁️",
  default: "🔷",
};

const getIcon = (label) => {
  const lower = label.toLowerCase();
  for (const key in ICONS) {
    if (lower.includes(key)) return ICONS[key];
  }
  return ICONS.default;
};

const nodeTypes = {
  custom: ({ data }) => {
    const tierStyle =
      TIER_STYLES[data.tier] || TIER_STYLES.core;

    return (
      <>
        <Handle
          type="target"
          position={Position.Left}
          style={{ background: "transparent", border: "none" }}
        />
        <div
          style={{
            padding: "20px 24px",
            background: tierStyle.background,
            border: `2px solid ${tierStyle.border}`,
            borderRadius: "14px",
            textAlign: "center",
            fontWeight: "600",
            fontSize: "14px",
            minWidth: "180px",
            boxShadow: tierStyle.shadow,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "10px",
            color: tierStyle.color,
            transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <div style={{ fontSize: "44px", lineHeight: "1" }}>
            {getIcon(data.label)}
          </div>
          <div style={{ letterSpacing: "0.2px" }}>
            {data.label}
          </div>
        </div>
        <Handle
          type="source"
          position={Position.Right}
          style={{ background: "transparent", border: "none" }}
        />
      </>
    );
  },
};

const getLayoutedElements = async (nodes, edges) => {
  const elkNodes = nodes.map((node) => ({
    id: node.id,
    width: 240,
    height: 120,
  }));

  const elkEdges = edges.map((edge) => ({
    id: edge.id,
    sources: [edge.source],
    targets: [edge.target],
  }));

  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.baseValue": "80",
      "elk.layered.spacing.nodeNodeBetweenLayers": "150",
    },
    children: elkNodes,
    edges: elkEdges,
  };

  const layout = await elk.layout(graph);

  return {
    nodes: layout.children.map((n) => {
      const original = nodes.find((node) => node.id === n.id);
      return {
        ...original,
        position: { x: n.x, y: n.y },
      };
    }),
    edges,
  };
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const BACKEND_URL =
    "https://unregenerating-talkatively-mamie.ngrok-free.dev/generate";

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);

    try {
      const res = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();

      const { nodes: layoutedNodes, edges: layoutedEdges } =
        await getLayoutedElements(data.nodes, data.edges);

      setNodes(
        layoutedNodes.map((n) => ({
          ...n,
          type: n.type === "group" ? "group" : "custom",
        }))
      );

      setEdges(
        layoutedEdges.map((e) => ({
          ...e,
          animated: e.animated,
          type: "smoothstep",
          style: { stroke: "#94a3b8", strokeWidth: 2.5 },
        }))
      );
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: "100vh", display: "flex", background: "#f8fafc" }}>
      {/* sidebar */}
      {/* canvas */}
      {/* (unchanged JSX omitted for brevity — everything else stays exactly the same) */}
    </div>
  );
}

export default App;
