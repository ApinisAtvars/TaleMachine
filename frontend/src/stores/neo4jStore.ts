import { defineStore } from 'pinia'
import { ref } from 'vue'

// The structure of the node object inside 'n' and 'm'
interface EntityProps {
  id: string
  [key: string]: any // allow other properties like description, role, traits
}

export interface ChapterNeo4j {
  title: string
  content: string
}

export interface Neo4jMessage {
  sender: 'user' | 'assistant'
  content: string
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
  const messages = ref<Neo4jMessage[]>([])
  const isLoading = ref(false)
  const areChaptersLoading = ref(false)
  const error = ref<string | null>(null)
  
  const selectedNode = ref<GraphNode | null>(null)
  const selectedLink = ref<GraphLink | null>(null)
  const chaptersForSelectedNode = ref<ChapterNeo4j[]>([])

  async function fetchMentionedChapters(nodeLabel: string, nodeName: string) {
    chaptersForSelectedNode.value = []
    if (!nodeLabel || !nodeName) return []
    try {
      areChaptersLoading.value = true
      const response = await fetch(`http://localhost:7890/neo4j/get_chapter_node_mapping`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ node_label: nodeLabel, node_name: nodeName })
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`)
      }
      const data = await response.json()
      chaptersForSelectedNode.value = data.map((chapter: any) => ({
        title: chapter.title,
        content: chapter.content
      }))
    } catch (err: any) {
      console.error(err)
      error.value = err.message || 'Unknown error'
      return []
    } finally {
      areChaptersLoading.value = false
    }
  }

  async function naturalLanguageQuery(query: string) {
    try {
      const response = await fetch(`http://localhost:7890/neo4j/natural_language_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`)
      }
      const data = await response.text() // This returns just the string as a response - super simple
      return data
    } catch (err: any) {
      console.error(err)
      error.value = err.message || 'Unknown error'
      return []
    }
  }

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
    fetchGraphData,
    fetchMentionedChapters,
    chaptersForSelectedNode,
    areChaptersLoading,
    messages,
    naturalLanguageQuery
  }
})