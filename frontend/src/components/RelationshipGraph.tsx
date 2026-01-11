import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { GraphData, GraphEdge, GraphNode } from "../types";
import { RELATIONSHIP_TYPES } from "../types";

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface SimEdge extends GraphEdge {
  sourceNode: SimNode;
  targetNode: SimNode;
}

export function RelationshipGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const edgesRef = useRef<SimEdge[]>([]);
  const dragNodeRef = useRef<SimNode | null>(null);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    api.graph.get()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const maybeCtx = canvas.getContext("2d");
    if (!maybeCtx) return;
    const ctx: CanvasRenderingContext2D = maybeCtx;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize nodes with random positions
    const nodes: SimNode[] = data.nodes.map((node) => ({
      ...node,
      x: centerX + (Math.random() - 0.5) * 300,
      y: centerY + (Math.random() - 0.5) * 300,
      vx: 0,
      vy: 0,
    }));
    nodesRef.current = nodes;

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // Create edges with node references
    const edges: SimEdge[] = data.edges
      .map((edge) => {
        const sourceNode = nodeMap.get(edge.source);
        const targetNode = nodeMap.get(edge.target);
        if (!sourceNode || !targetNode) return null;
        return { ...edge, sourceNode, targetNode };
      })
      .filter((e): e is SimEdge => e !== null);
    edgesRef.current = edges;

    // Force simulation parameters
    const repulsion = 5000;
    const springStrength = 0.05;
    const baseSpringLength = 150;
    const damping = 0.9;
    const centerPull = 0.01;

    function simulate() {
      const nodes = nodesRef.current;
      const edges = edgesRef.current;

      // Reset forces
      for (const node of nodes) {
        node.vx = 0;
        node.vy = 0;
      }

      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }

      // Spring forces for edges - closer relationships = shorter springs
      // Weight is 1-10, normalize to 0-1 for calculations
      for (const edge of edges) {
        const dx = edge.targetNode.x - edge.sourceNode.x;
        const dy = edge.targetNode.y - edge.sourceNode.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        // Higher weight (1-10) = shorter ideal length
        // Normalize: weight 10 -> 0.5x length, weight 1 -> 1.4x length
        const normalizedWeight = edge.closeness_weight / 10;
        const idealLength = baseSpringLength * (1.5 - normalizedWeight);
        const displacement = dist - idealLength;
        const force = springStrength * displacement;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        edge.sourceNode.vx += fx;
        edge.sourceNode.vy += fy;
        edge.targetNode.vx -= fx;
        edge.targetNode.vy -= fy;
      }

      // Pull toward center
      for (const node of nodes) {
        node.vx += (centerX - node.x) * centerPull;
        node.vy += (centerY - node.y) * centerPull;
      }

      // Apply velocities with damping (skip dragged node)
      for (const node of nodes) {
        if (node === dragNodeRef.current) continue;
        node.x += node.vx * damping;
        node.y += node.vy * damping;
        // Keep within bounds
        node.x = Math.max(30, Math.min(width - 30, node.x));
        node.y = Math.max(30, Math.min(height - 30, node.y));
      }
    }

    function getEdgeColor(weight: number): string {
      // Interpolate from light gray (distant) to dark blue (close)
      // weight is 1-10, normalize to 0-1
      const normalized = weight / 10;
      const hue = 220;
      const saturation = 70;
      const lightness = 80 - normalized * 40;
      return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    }

    function draw(context: CanvasRenderingContext2D) {
      const nodes = nodesRef.current;
      const edges = edgesRef.current;

      context.clearRect(0, 0, width, height);

      // Draw edges
      for (const edge of edges) {
        // Weight is 1-10, scale line width accordingly
        const lineWidth = 1 + (edge.closeness_weight / 10) * 3;
        context.strokeStyle = getEdgeColor(edge.closeness_weight);
        context.lineWidth = lineWidth;
        context.beginPath();
        context.moveTo(edge.sourceNode.x, edge.sourceNode.y);
        context.lineTo(edge.targetNode.x, edge.targetNode.y);
        context.stroke();

        // Draw relationship type label at midpoint
        const midX = (edge.sourceNode.x + edge.targetNode.x) / 2;
        const midY = (edge.sourceNode.y + edge.targetNode.y) / 2;
        context.fillStyle = "#666";
        context.font = "10px sans-serif";
        context.textAlign = "center";
        const typeInfo = RELATIONSHIP_TYPES.find(t => t.value === edge.relationship_type);
        const label = typeInfo?.displayName || edge.relationship_type;
        context.fillText(label, midX, midY - 5);
      }

      // Draw nodes
      for (const node of nodes) {
        const isSelected = node === selectedNode;
        const radius = isSelected ? 25 : 20;

        // Node circle
        context.beginPath();
        context.arc(node.x, node.y, radius, 0, Math.PI * 2);
        context.fillStyle = isSelected ? "#0066cc" : "#fff";
        context.fill();
        context.strokeStyle = "#0066cc";
        context.lineWidth = 2;
        context.stroke();

        // Node label
        context.fillStyle = isSelected ? "#fff" : "#333";
        context.font = "12px sans-serif";
        context.textAlign = "center";
        context.textBaseline = "middle";
        const name = node.name.length > 10 ? node.name.slice(0, 9) + "…" : node.name;
        context.fillText(name, node.x, node.y);
      }
    }

    function animate() {
      simulate();
      draw(ctx);
      animationRef.current = requestAnimationFrame(animate);
    }

    animate();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [data, selectedNode]);

  // Mouse interaction handlers
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function getNodeAtPosition(x: number, y: number): SimNode | null {
      for (const node of nodesRef.current) {
        const dx = x - node.x;
        const dy = y - node.y;
        if (dx * dx + dy * dy < 400) {
          return node;
        }
      }
      return null;
    }

    function handleMouseDown(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const node = getNodeAtPosition(x, y);
      if (node) {
        dragNodeRef.current = node;
        setSelectedNode(node);
      }
    }

    function handleMouseMove(e: MouseEvent) {
      if (!dragNodeRef.current) return;
      const rect = canvas!.getBoundingClientRect();
      dragNodeRef.current.x = e.clientX - rect.left;
      dragNodeRef.current.y = e.clientY - rect.top;
    }

    function handleMouseUp() {
      dragNodeRef.current = null;
    }

    canvas.addEventListener("mousedown", handleMouseDown);
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseup", handleMouseUp);
    canvas.addEventListener("mouseleave", handleMouseUp);

    return () => {
      canvas.removeEventListener("mousedown", handleMouseDown);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseup", handleMouseUp);
      canvas.removeEventListener("mouseleave", handleMouseUp);
    };
  }, []);

  if (loading) return <p>Loading graph...</p>;
  if (error) return <div className="error">{error}</div>;
  if (!data) return <p>No data available</p>;

  return (
    <div className="graph-container">
      <div className="header">
        <h1>Relationship Graph</h1>
      </div>
      <p className="graph-hint">
        Drag nodes to reposition. Closer relationships have shorter, darker edges.
      </p>
      <canvas
        ref={canvasRef}
        width={900}
        height={600}
        style={{
          border: "1px solid var(--color-border)",
          borderRadius: "8px",
          background: "var(--color-bg)",
          cursor: "grab",
        }}
      />
      {selectedNode && (
        <div className="selected-info">
          <h3>{selectedNode.name}</h3>
          {selectedNode.current_job && <p>Job: {selectedNode.current_job}</p>}
          <a href={`/contacts/${selectedNode.id}`}>View details</a>
        </div>
      )}
      <div className="legend">
        <h4>Relationship Closeness (1-10)</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-line" style={{ background: getEdgeColorCSS(10), height: "4px" }}></span>
            <span>10 - Very Close (Spouse, Partner)</span>
          </div>
          <div className="legend-item">
            <span className="legend-line" style={{ background: getEdgeColorCSS(7), height: "3px" }}></span>
            <span>7 - Close (Family, Best Friend)</span>
          </div>
          <div className="legend-item">
            <span className="legend-line" style={{ background: getEdgeColorCSS(4), height: "2px" }}></span>
            <span>4 - Moderate (Friend, Colleague)</span>
          </div>
          <div className="legend-item">
            <span className="legend-line" style={{ background: getEdgeColorCSS(2), height: "1px" }}></span>
            <span>2 - Distant (Acquaintance)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function getEdgeColorCSS(weight: number): string {
  // weight is 1-10, normalize to 0-1
  const normalized = weight / 10;
  const hue = 220;
  const saturation = 70;
  const lightness = 80 - normalized * 40;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}
