import { defineStore } from 'pinia'
import { ref } from 'vue'

// The structure of the node object inside 'n' and 'm'
interface EntityProps {
  id: string
  [key: string]: any // allow other properties like description, role, traits
}


export interface Neo4jRawResult {
  n: EntityProps
  "labels(n)": string[]
  // r is [StartNode, TypeString, EndNode]
  r: [EntityProps, string, EntityProps]
  m: EntityProps
  "labels(m)": string[]
}

// --- D3 Graph Types ---

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  labels: string[]
  properties: Record<string, any>
  // D3 internal coordinates
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  id: string
  source: string | GraphNode // D3 expects string ID initially
  target: string | GraphNode
  type: string
  properties?: Record<string, any> // The current query doesn't return relationship properties
}

export const useNeo4jStore = defineStore('neo4j', () => {
  const nodes = ref<GraphNode[]>([])
  const links = ref<GraphLink[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  const selectedNode = ref<GraphNode | null>(null)
  const selectedLink = ref<GraphLink | null>(null)

  async function fetchGraphData(databaseName: string) {
    if (!databaseName) return

    isLoading.value = true
    error.value = null
    selectedNode.value = null
    selectedLink.value = null

    try {
      // Encode the database name to handle spaces or special chars if necessary
      const response = await fetch(`http://localhost:7890/neo4j/get_all_nodes_relationships/${databaseName}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`)
      }

      const rawData: Neo4jRawResult[] = await response.json()
      processData(rawData)
    } catch (err: any) {
      console.error(err)
      error.value = err.message || 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  function processData(data: Neo4jRawResult[]) {
    const nodeMap = new Map<string, GraphNode>()
    const linkMap = new Map<string, GraphLink>()

    data.forEach(row => {
      // 1. Process Source Node (n)
      // The JSON uses "id" inside the n object as the unique identifier
      const sourceId = row.n.id
      if (!nodeMap.has(sourceId)) {
        nodeMap.set(sourceId, {
          id: sourceId,
          labels: row["labels(n)"],
          properties: row.n
        })
      }

      // 2. Process Target Node (m)
      const targetId = row.m.id
      if (!nodeMap.has(targetId)) {
        nodeMap.set(targetId, {
          id: targetId,
          labels: row["labels(m)"],
          properties: row.m
        })
      }

      // 3. Process Relationship (r)
      const relType = row.r[1] 

      // Create a unique ID for the link
      const linkId = `${sourceId}_${relType}_${targetId}`

      if (!linkMap.has(linkId)) {
        linkMap.set(linkId, {
          id: linkId,
          source: sourceId,
          target: targetId,
          type: relType,
          properties: {}
        })
      }
    })

    nodes.value = Array.from(nodeMap.values())
    links.value = Array.from(linkMap.values())
  }

  return {
    nodes,
    links,
    isLoading,
    error,
    selectedNode,
    selectedLink,
    fetchGraphData
  }
})