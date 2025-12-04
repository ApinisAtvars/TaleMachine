<template>
  <div class="relative w-full h-[800px] border rounded-xl bg-slate-50 overflow-hidden shadow-sm font-sans">
    
    <!-- Loading / Error States -->
    <div v-if="store.isLoading" class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-800 border-t-transparent"></div>
      <span class="mt-2 text-sm font-medium text-slate-600">Loading Knowledge Graph...</span>
    </div>

    <div v-if="store.error" class="absolute inset-0 z-20 flex items-center justify-center bg-white/90">
      <div class="text-red-500 font-medium px-4 py-2 bg-red-50 rounded-lg border border-red-100">
        {{ store.error }}
      </div>
    </div>

    <!-- D3 Container -->
    <div ref="containerRef" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

    <!-- Details Sidebar -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-x-10"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-10"
    >
      <div v-if="store.selectedNode || store.selectedLink" 
           class="absolute top-4 right-4 w-80 max-h-[90%] overflow-y-auto z-10 rounded-lg border bg-white shadow-xl flex flex-col">
        
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b bg-slate-50">
          <h3 class="font-semibold text-sm uppercase tracking-wider text-slate-700">
            {{ store.selectedNode ? 'Node Details' : 'Relationship' }}
          </h3>
          <button @click="clearSelection" class="text-slate-400 hover:text-slate-700 transition-colors">
            <!-- X Icon -->
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <div class="p-4 space-y-4">
          
          <!-- Node Content -->
          <div v-if="store.selectedNode">
            <!-- Identity -->
            <div class="mb-4">
               <h2 class="text-xl font-bold text-slate-900 leading-tight">
                 {{ store.selectedNode.properties.id }}
               </h2>
               <div class="flex flex-wrap gap-1 mt-2">
                <span v-for="label in store.selectedNode.labels" :key="label"
                      class="px-2.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full border border-blue-200">
                  {{ label }}
                </span>
              </div>
            </div>

            <!-- Specific Properties Highlight -->
            <div v-if="store.selectedNode.properties.description" class="bg-slate-50 p-3 rounded-md border border-slate-100 text-sm text-slate-600 italic mb-4">
              "{{ store.selectedNode.properties.description }}"
            </div>

            <!-- Key-Value Table -->
            <div class="space-y-3">
              <div v-for="(val, key) in filterProps(store.selectedNode.properties)" :key="key" 
                   class="text-sm group">
                <span class="text-xs font-bold text-slate-400 uppercase block mb-0.5 group-hover:text-slate-600 transition-colors">
                  {{ key }}
                </span>
                <span class="text-slate-700 break-words leading-relaxed block bg-slate-50 px-2 py-1 rounded border border-slate-100">
                  {{ val }}
                </span>
              </div>
            </div>
          </div>

          <!-- Link Content -->
          <div v-if="store.selectedLink">
             <div class="text-center py-4 bg-slate-50 rounded border border-slate-100 mb-4">
               <span class="text-xs font-bold text-slate-400 block mb-1">TYPE</span>
               <span class="text-lg font-mono font-bold text-slate-700">{{ store.selectedLink.type }}</span>
             </div>
             
             <div class="text-xs text-slate-500 text-center">
               Connected <br/>
               <span class="font-semibold text-slate-700">{{ getId(store.selectedLink.source) }}</span>
               <span class="mx-1">→</span>
               <span class="font-semibold text-slate-700">{{ getId(store.selectedLink.target) }}</span>
             </div>
          </div>

        </div>
      </div>
    </transition>

    <!-- Controls / Legend -->
    <div class="absolute bottom-4 left-4 flex flex-col gap-2">
      <div class="bg-white/90 backdrop-blur border rounded-lg shadow-sm p-3 text-xs text-slate-600 min-w-[150px]">
        <div class="font-bold mb-2 text-slate-800">Graph Controls</div>
        <div class="flex items-center gap-2 mb-1">
          <span class="w-4 h-4 flex items-center justify-center bg-slate-100 rounded border">🖱</span>
          <span>Drag to move</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-4 flex items-center justify-center bg-slate-100 rounded border">🔍</span>
          <span>Scroll to zoom</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as d3 from 'd3'
import { useNeo4jStore, type GraphNode, type GraphLink } from '@/stores/neo4jStore'


const store = useNeo4jStore()
const containerRef = ref<HTMLElement | null>(null)

// --- D3 Variables ---
let simulation: d3.Simulation<GraphNode, GraphLink> | null = null
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
let g: d3.Selection<SVGGElement, unknown, null, undefined>

// --- Configuration ---
const NODE_RADIUS = 24
const LINK_LENGTH = 180
// A Neo4j-inspired color palette for common labels
const colorScale = d3.scaleOrdinal()
  .domain(["Person", "Location", "Item", "Technology", "Event", "Organization"])
  .range(["#fca5a5", "#93c5fd", "#fdba74", "#d8b4fe", "#86efac", "#fcd34d"])
// Fallback color scheme
const fallbackColor = d3.scaleOrdinal(d3.schemeTableau10)

onMounted(async () => {
    initGraph()
    await store.fetchGraphData("pristinechip")
})

onUnmounted(() => {
  if (simulation) simulation.stop()
})

watch(() => store.nodes, (newNodes) => {
  if (newNodes.length > 0) updateGraph()
})

function initGraph() {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  svg = d3.select(containerRef.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', [0, 0, width, height])
    .style('background-color', '#f8fafc')

  // Zoom group
  g = svg.append('g')

  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 5])
    .on('zoom', (event) => g.attr('transform', event.transform))
  
  svg.call(zoom).on('dblclick.zoom', null) // Disable double click zoom

  // Marker for arrows
  svg.append('defs').append('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', NODE_RADIUS + 6) 
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#94a3b8')

  simulation = d3.forceSimulation<GraphNode, GraphLink>()
    .force('link', d3.forceLink<GraphNode, GraphLink>().id(d => d.id).distance(LINK_LENGTH))
    .force('charge', d3.forceManyBody().strength(-500))
    .force('collide', d3.forceCollide(NODE_RADIUS + 10))
    .force('center', d3.forceCenter(width / 2, height / 2))
}

function updateGraph() {
  if (!simulation) return

  // 1. Links
  const link = g.selectAll<SVGLineElement, GraphLink>('.link')
    .data(store.links, d => d.id)
    .join('line')
    .attr('class', 'link')
    .attr('stroke', '#cbd5e1')
    .attr('stroke-width', 2)
    .attr('marker-end', 'url(#arrow)')
    .style('cursor', 'pointer')
    .on('click', (e, d) => {
      e.stopPropagation()
      store.selectedLink = d
      store.selectedNode = null
    })
    .on('mouseenter', function() { d3.select(this).attr('stroke', '#64748b').attr('stroke-width', 3) })
    .on('mouseleave', function() { 
      if (store.selectedLink?.id !== (d3.select(this).datum() as GraphLink).id) {
        d3.select(this).attr('stroke', '#cbd5e1').attr('stroke-width', 2)
      }
    })

  // 2. Link Labels
  const linkLabel = g.selectAll<SVGTextElement, GraphLink>('.link-label')
    .data(store.links, d => d.id)
    .join('text')
    .attr('class', 'link-label')
    .text(d => d.type)
    .attr('text-anchor', 'middle')
    .attr('dy', -5)
    .style('font-size', '10px')
    .style('fill', '#64748b')
    .style('font-weight', '600')
    .style('pointer-events', 'none')

    // Link label background (for readability)
    .call(text => text.clone(true).lower()
      .attr("stroke", "#f8fafc")
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round"));

  // 3. Nodes
  const node = g.selectAll<SVGGElement, GraphNode>('.node')
    .data(store.nodes, d => d.id)
    .join('g')
    .attr('class', 'node')
    .call(d3.drag<SVGGElement, GraphNode>()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded)
    )
    .on('click', (e, d) => {
      e.stopPropagation()
      store.selectedNode = d
      store.selectedLink = null
    })

  // Circle
  node.append('circle')
    .attr('r', NODE_RADIUS)
    .attr('fill', d => {
       const label = d.labels[0] || 'Unknown';
       return (colorScale(label) as string) || fallbackColor(label);
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'grab')
    .style('filter', 'drop-shadow(0 2px 4px rgb(0 0 0 / 0.1))')

  // Label (First 2 chars or Icon could go here)
  node.append('text')
    .text(d => d.properties.id.substring(0, 2).toUpperCase())
    .attr('text-anchor', 'middle')
    .attr('dy', 4)
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('fill', 'rgba(0,0,0,0.6)')
    .style('pointer-events', 'none')

  // Full Name Label (Below Node)
  node.append('text')
    .text(d => d.properties.id)
    .attr('text-anchor', 'middle')
    .attr('dy', NODE_RADIUS + 14)
    .style('font-size', '11px')
    .style('fill', '#475569')
    .style('pointer-events', 'none')
    .style('text-shadow', '1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff')

  simulation.nodes(store.nodes).on('tick', () => {
    link
      .attr('x1', d => (d.source as GraphNode).x!)
      .attr('y1', d => (d.source as GraphNode).y!)
      .attr('x2', d => (d.target as GraphNode).x!)
      .attr('y2', d => (d.target as GraphNode).y!)

    linkLabel
      .attr('x', d => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
      .attr('y', d => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  simulation.force<d3.ForceLink<GraphNode, GraphLink>>('link')!.links(store.links)
  simulation.alpha(1).restart()
}

// Helpers
function clearSelection() {
  store.selectedNode = null
  store.selectedLink = null
}

function getId(node: string | GraphNode): string {
  return typeof node === 'string' ? node : node.id
}

// Don't show ID twice in the list of properties
function filterProps(props: Record<string, any>) {
  const { id, ...rest } = props
  return rest
}

// D3 Dragging
function dragStarted(event: any, d: GraphNode) {
  if (!event.active && simulation) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event: any, d: GraphNode) {
  d.fx = event.x
  d.fy = event.y
}

function dragEnded(event: any, d: GraphNode) {
  if (!event.active && simulation) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}
</script>