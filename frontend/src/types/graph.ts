// Represents the raw structure returned by your Python Backend
export interface Neo4jRawResult {
  n: Neo4jNodeRaw;
  "labels(n)": string[];
  r: Neo4jRelRaw;
  m: Neo4jNodeRaw;
  "labels(m)": string[];
}

interface Neo4jNodeRaw {
  elementId: string; // Neo4j 5+ uses elementId. Older uses id (int)
  id?: number; 
  properties: Record<string, any>;
}

interface Neo4jRelRaw {
  elementId: string;
  id?: number;
  type: string;
  startNodeElementId: string;
  endNodeElementId: string;
  properties: Record<string, any>;
}

// The clean structure our D3 Graph will use
export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  // properties for D3 simulation
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  id: string;
  source: string | GraphNode; // D3 converts string ID to Node object
  target: string | GraphNode;
  type: string;
  properties: Record<string, any>;
}