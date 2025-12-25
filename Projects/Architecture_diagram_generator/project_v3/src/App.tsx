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
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import ELK from "elkjs/lib/elk.bundled.js";

const elk = new ELK();

const TIER_STYLES = {
  frontend: { bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", border: "#667eea" },
  api: { bg: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", border: "#f093fb" },
  core: { bg: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", border: "#4facfe" },
  data: { bg: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", border: "#43e97b" },
  external: { bg: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", border: "#fa709a" },
};

const ICONS = {
  cdn: "🌐", mobile: "📱", web: "🖥️", frontend: "🌐", api: "🔌", gateway: "🔌",
  "load balancer": "⚖️", auth: "🔒", service: "⚙️", server: "🖥️",
  database: "🗄️", postgres: "🗄️", redis: "⚡", cache: "⚡", kafka: "📨",
  queue: "📨", payment: "💳", notification: "🔔", external: "☁️", default: "🔷",
};

const getIcon = (label: string) => {
  const l = label.toLowerCase();
  for (const k in ICONS) if (l.includes(k)) return ICONS[k as keyof typeof ICONS];
  return ICONS.default;
};

const nodeTypes = {
  custom: ({ data }: any) => {
    const style = TIER_STYLES[data.tier as keyof typeof TIER_STYLES] || TIER_STYLES.core;
    return (
      <>
        <Handle type="target" position={Position.Left} style={{ background: "transparent", border: "none" }} />
        <div style={{
          padding: "20px 24px",
          background: style.bg,
          border: `2px solid ${style.border}`,
          borderRadius: "14px",
          textAlign: "center",
          fontWeight: "600",
          fontSize: "14px",
          minWidth: "180px",
          boxShadow: "0 12px 32px rgba(0,0,0,0.25)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "10px",
          color: "#ffffff",
        }}>
          <div style={{ fontSize: "44px" }}>{getIcon(data.label)}</div>
          <div style={{ fontWeight: "700" }}>{data.label}</div>
        </div>
        <Handle type="source" position={Position.Right} style={{ background: "transparent", border: "none" }} />
      </>
    );
  },
  group: ({ data }: any) => (
    <div style={{
      width: "100%",
      height: "100%",
      borderRadius: "24px",
      border: "3px solid #667eea",
      background: "rgba(102, 126, 234, 0.08)",
      padding: "140px 80px 80px 80px",
      position: "relative",
    }}>
      <div style={{
        position: "absolute",
        top: "24px",
        left: "50%",
        transform: "translateX(-50%)",
        fontSize: "20px",
        fontWeight: "800",
        color: "#ffffff",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: "10px 32px",
        borderRadius: "12px",
        boxShadow: "0 6px 20px rgba(102, 126, 234, 0.35)",
        whiteSpace: "nowrap",
      }}>
        {data.label}
      </div>
    </div>
  ),
};

const getLayoutedElements = async (nodes: Node[], edges: Edge[], darkMode: boolean) => {
  const elkNodes: any[] = [];
  const elkEdges: any[] = [];

  const groupChildren: { [key: string]: string[] } = {};

  // First pass: collect groups and their children IDs
  nodes.forEach((node) => {
    if (node.type === "group") {
      groupChildren[node.id] = [];
      elkNodes.push({
        id: node.id,
        layoutOptions: {
          "elk.algorithm": "layered",
          "elk.direction": "RIGHT",
          "elk.spacing.baseValue": "100",
          "elk.layered.spacing.nodeNodeBetweenLayers": "200",
          "elk.padding": "[top=140,left=80,bottom=80,right=80]",
          "elk.edgeRouting": "ORTHOGONAL",
        },
        children: [],
        edges: [],
      });
    }
  });

  // Second pass: add regular nodes and assign to groups
  nodes.forEach((node) => {
    if (node.type !== "group") {
      const elkNode = {
        id: node.id,
        width: 240,
        height: 160,
      };
      if (node.parentId && groupChildren[node.parentId]) {
        groupChildren[node.parentId].push(node.id);
      } else {
        elkNodes.push(elkNode);
      }
    }
  });

  // Attach children to group nodes
  elkNodes.forEach((gNode) => {
    if (groupChildren[gNode.id]) {
      gNode.children = groupChildren[gNode.id].map(id => ({ id, width: 240, height: 160 }));
    }
  });

  // Add all edges
  edges.forEach((edge, i) => {
    elkEdges.push({
      id: `e-${i}`,
      sources: [edge.source],
      targets: [edge.target],
    });
  });

  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.layered.spacing.baseValue": "150",
      "elk.layered.spacing.nodeNodeBetweenLayers": "300",
      "elk.spacing.componentComponent": "250",
      "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
      "elk.edgeRouting": "ORTHOGONAL",
    },
    children: elkNodes,
    edges: elkEdges,
  };

  try {
    const layout = await elk.layout(graph);

    // Map positions back to original nodes
    const newNodes = nodes.map((node) => {
      const findInLayout = (children: any[]): any => {
        for (const child of children) {
          if (child.id === node.id) return child;
          if (child.children) {
            const found = findInLayout(child.children);
            if (found) return found;
          }
        }
        return null;
      };

      const laidOutNode = findInLayout(layout.children || []);

      if (!laidOutNode) return node;

      if (node.type === "group") {
        return {
          ...node,
          position: { x: laidOutNode.x || 0, y: laidOutNode.y || 0 },
          style: {
            width: laidOutNode.width || 600,
            height: laidOutNode.height || 500,
            backgroundColor: darkMode ? "rgba(30, 41, 59, 0.3)" : "rgba(240, 245, 255, 0.6)",
            border: "3px solid #667eea",
            borderRadius: "24px",
            boxShadow: darkMode ? "0 12px 48px rgba(0,0,0,0.4)" : "0 12px 48px rgba(102, 126, 234, 0.12)",
          },
        };
      }

      // Find parent group position
      const parentGroup = layout.children?.find((g: any) =>
        g.children?.some((c: any) => c.id === node.id)
      );

      const parentX = parentGroup?.x || 0;
      const parentY = parentGroup?.y || 0;

      return {
        ...node,
        type: "custom",
        extent: node.parentId ? ("parent" as const) : undefined,
        position: {
          x: laidOutNode.x + parentX,
          y: laidOutNode.y + parentY,
        },
      };
    });

    return { nodes: newNodes, edges };
  } catch (err) {
    console.error("ELK failed:", err);
    return { nodes, edges };
  }
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);

  const BACKEND_URL = "https://unregenerating-talkatively-mamie.ngrok-free.dev/generate";

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

      const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(
        data.nodes as Node[],
        data.edges as Edge[],
        darkMode
      );

      setNodes(layoutedNodes);
      setEdges(
        layoutedEdges.map((e: any, i: number) => ({
          ...e,
          id: e.id || `edge-${i}`,
          type: "smoothstep",
          style: { stroke: darkMode ? "#94a3b8" : "#64748b", strokeWidth: 3 },
          markerEnd: { type: "arrowclosed", color: darkMode ? "#94a3b8" : "#64748b" },
          label: e.label || "",
          labelStyle: { fill: darkMode ? "#e2e8f0" : "#1e293b", fontSize: 13, fontWeight: 700 },
          labelBgStyle: { fill: darkMode ? "rgba(30,41,59,0.9)" : "rgba(255,255,255,0.9)" },
          labelBgPadding: [8, 12],
          labelBgBorderRadius: 8,
        }))
      );
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: "100vh", display: "flex", background: darkMode ? "#0f172a" : "#f8fafc" }}>
      <div style={{
        width: "380px",
        padding: "28px 24px",
        background: darkMode ? "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)" : "#ffffff",
        borderRight: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        overflowY: "auto",
      }}>
        <h1 style={{
          fontSize: "26px",
          fontWeight: "700",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}>
          Architecture AI
        </h1>
        <p style={{ fontSize: "13px", color: darkMode ? "#94a3b8" : "#64748b" }}>
          Generate system architecture diagrams from natural language
        </p>

        <textarea
          rows={9}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., A simple web app with browser, frontend, API gateway, auth service, backend, and database"
          style={{
            padding: "14px",
            borderRadius: "10px",
            border: `1.5px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
            background: darkMode ? "#1e293b" : "#ffffff",
            color: darkMode ? "#e2e8f0" : "#334155",
            fontSize: "14px",
            resize: "vertical",
          }}
        />

        <button
          onClick={generate}
          disabled={loading}
          style={{
            padding: "14px",
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "#fff",
            border: "none",
            borderRadius: "10px",
            fontWeight: "600",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Generating..." : "Generate Diagram"}
        </button>

        <button
          onClick={() => setDarkMode(!darkMode)}
          style={{
            padding: "12px",
            background: darkMode ? "#4c1d95" : "#e2e8f0",
            color: darkMode ? "#fff" : "#475569",
            border: "none",
            borderRadius: "10px",
          }}
        >
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>

        {nodes.length > 0 && (
          <div style={{ padding: "14px", background: "rgba(102,126,234,0.1)", borderRadius: "10px" }}>
            <p style={{ margin: 0, fontSize: "12px", fontWeight: "600" }}>
              Generated {nodes.length} components • {edges.length} connections
            </p>
          </div>
        )}
      </div>

      <div style={{ flex: 1 }}>
        {nodes.length === 0 ? (
          <div style={{
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#64748b",
            fontSize: "18px",
          }}>
            Enter a description and generate your architecture diagram
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
          >
            <Background color={darkMode ? "#334155" : "#cbd5e1"} gap={20} />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}

export default App;