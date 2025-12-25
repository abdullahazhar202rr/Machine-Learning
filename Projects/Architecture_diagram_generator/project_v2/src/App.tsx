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
    color: "#ffffff"
  },
  api: {
    background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    border: "#f093fb",
    shadow: "0 12px 32px rgba(240, 147, 251, 0.35)",
    color: "#ffffff"
  },
  core: {
    background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    border: "#4facfe",
    shadow: "0 12px 32px rgba(79, 172, 254, 0.35)",
    color: "#ffffff"
  },
  data: {
    background: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    border: "#43e97b",
    shadow: "0 12px 32px rgba(67, 233, 123, 0.35)",
    color: "#ffffff"
  },
  external: {
    background: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    border: "#fa709a",
    shadow: "0 12px 32px rgba(250, 112, 154, 0.35)",
    color: "#ffffff"
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

const getIcon = (label: string) => {
  const lower = label.toLowerCase();
  for (const key in ICONS) {
    if (lower.includes(key)) return ICONS[key as keyof typeof ICONS];
  }
  return ICONS.default;
};

const nodeTypes = {
  custom: ({ data }: any) => {
    const tierStyle = TIER_STYLES[data.tier as keyof typeof TIER_STYLES] || TIER_STYLES.core;
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
          <div style={{ letterSpacing: "0.2px", color: "#1e293b", fontWeight: "700" }}>{data.label}</div>
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

const getLayoutedElements = async (nodes: any[], edges: any[]) => {
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
    nodes: layout.children!.map((n) => {
      const original = nodes.find((node) => node.id === n.id);
      return {
        ...original,
        position: { x: n.x!, y: n.y! },
      };
    }),
    edges,
  };
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

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
        data.nodes,
        data.edges
      );

            setNodes(
        layoutedNodes.map((n) => {
          if (n.type === "group") {
            return {
              ...n,
              style: {
                backgroundColor: darkMode ? "rgba(30, 41, 59, 0.4)" : "rgba(240, 245, 255, 0.6)",
                border: "3px solid #667eea",
                borderRadius: "20px",
                padding: 40, // Space inside the group so children don't touch the border
                boxShadow: darkMode ? "0 8px 32px rgba(0, 0, 0, 0.3)" : "0 8px 32px rgba(102, 126, 234, 0.2)",
              },
              data: {
                ...n.data,
                label: (
                  <div
  style={{
    fontSize: "22px",
    fontWeight: "800",
    color: darkMode ? "#e2e8f0" : "#ffffff",  // Only one color here
    textAlign: "center",
    padding: "12px 20px",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    borderRadius: "12px",
    marginBottom: "20px",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
  }}
>
  {n.data.label}
</div>
                ),
              },
            };
          }

          // Regular nodes → use your beautiful custom style
          return {
            ...n,
            type: "custom",
          };
        })
      );

      // EXACTLY SAME LOGIC AS YOUR ORIGINAL CODE for edges
      // Only added visible labels + dark mode support
      setEdges(
        layoutedEdges.map((e) => ({
          ...e,
          animated: e.animated,
          type: "smoothstep",
          style: { stroke: darkMode ? "#94a3b8" : "#94a3b8", strokeWidth: 2.5 },
          // New: Make edge labels clearly visible
          label: e.label || "",
          labelStyle: {
            fill: darkMode ? "#e2e8f0" : "#1e293b",
            fontSize: 16,
            fontWeight: 700,
          },
          labelBgStyle: {
            fill: darkMode ? "rgba(30, 41, 59, 0.85)" : "rgba(255, 255, 255, 0.9)",
          },
          labelBgPadding: [6, 8],
          labelBgBorderRadius: 6,
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
      <div
        style={{
          width: "380px",
          padding: "28px 24px",
          background: darkMode
            ? "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)"
            : "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
          borderRight: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          boxShadow: "2px 0 16px rgba(0, 0, 0, 0.05)",
          overflowY: "auto",
          color: darkMode ? "#e2e8f0" : "#334155",
        }}
      >
        <div>
          <h1
            style={{
              margin: "0 0 8px 0",
              fontSize: "26px",
              fontWeight: "700",
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              letterSpacing: "-0.5px",
            }}
          >
            Architecture AI
          </h1>
          <p style={{ margin: 0, fontSize: "13px", color: darkMode ? "#94a3b8" : "#64748b", fontWeight: "500" }}>
            Generate system architecture diagrams from natural language
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <label
            style={{
              fontSize: "13px",
              fontWeight: "600",
              color: darkMode ? "#cbd5e1" : "#334155",
              letterSpacing: "0.4px",
              textTransform: "uppercase",
            }}
          >
            System Description
          </label>
          <textarea
            rows={9}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your architecture: e.g., 'Build an e-commerce platform with React frontend, Node API, PostgreSQL database, Redis cache, and Stripe payment integration'"
            style={{
              width: "100%",
              padding: "14px",
              fontSize: "14px",
              borderRadius: "10px",
              border: `1.5px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
              background: darkMode ? "#1e293b" : "#ffffff",
              color: darkMode ? "#e2e8f0" : "#334155",
              fontFamily: "inherit",
              lineHeight: "1.5",
              transition: "all 0.2s ease",
              outline: "none",
              resize: "vertical",
            } as any}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "#667eea";
              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(102, 126, 234, 0.08)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = darkMode ? "#334155" : "#e2e8f0";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
        </div>

        <button
          onClick={generate}
          disabled={loading}
          style={{
            padding: "14px 20px",
            fontSize: "15px",
            fontWeight: "600",
            background: loading
              ? "#cbd5e1"
              : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "#ffffff",
            border: "none",
            borderRadius: "10px",
            cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.3s ease",
            boxShadow: loading
              ? "0 2px 8px rgba(0, 0, 0, 0.08)"
              : "0 4px 16px rgba(102, 126, 234, 0.35)",
            letterSpacing: "0.3px",
          }}
          onMouseEnter={(e) => {
            if (!loading) {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 8px 24px rgba(102, 126, 234, 0.45)";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = loading
              ? "0 2px 8px rgba(0, 0, 0, 0.08)"
              : "0 4px 16px rgba(102, 126, 234, 0.35)";
          }}
        >
          {loading ? "Generating..." : "Generate Diagram"}
        </button>

        <button
          onClick={() => setDarkMode(!darkMode)}
          style={{
            padding: "12px 20px",
            fontSize: "14px",
            fontWeight: "600",
            background: darkMode ? "#4c1d95" : "#e2e8f0",
            color: darkMode ? "#ffffff" : "#475569",
            border: "none",
            borderRadius: "10px",
            cursor: "pointer",
            transition: "all 0.3s ease",
          }}
        >
          {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
        </button>

        {nodes.length > 0 && (
          <div
            style={{
              padding: "14px",
              background: darkMode
                ? "rgba(102, 126, 234, 0.15)"
                : "linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)",
              borderRadius: "10px",
              border: `1px solid ${darkMode ? "rgba(102, 126, 234, 0.3)" : "rgba(102, 126, 234, 0.2)"}`,
            }}
          >
            <p style={{ margin: 0, fontSize: "12px", color: darkMode ? "#cbd5e1" : "#334155", fontWeight: "600" }}>
              Generated {nodes.length} components with {edges.length} connections
            </p>
          </div>
        )}
      </div>

      <div
        style={{
          flex: 1,
          position: "relative",
          overflow: "hidden",
          background: darkMode
            ? "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
            : "linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%)",
        }}
      >
        {nodes.length === 0 ? (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: darkMode ? "#64748b" : "#94a3b8",
              fontSize: "16px",
              fontWeight: "500",
            }}
          >
            Enter a description and click Generate to visualize your architecture
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
            style={{ width: "100%", height: "100%" }}
          >
            <Background gap={16} color={darkMode ? "#334155" : "#cbd5e1"} size={1} />
            <Controls
              style={{
                button: {
                  background: darkMode ? "#1e293b" : "#ffffff",
                  border: `1px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
                  color: darkMode ? "#e2e8f0" : "#475569",
                } as any,
              }}
            />
            <MiniMap
              pannable
              zoomable
              style={{
                background: darkMode ? "#1e293b" : "#ffffff",
                border: `1px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)",
              }}
              maskColor={darkMode ? "rgba(30, 41, 59, 0.6)" : "rgba(102, 126, 234, 0.08)"}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}

export default App;