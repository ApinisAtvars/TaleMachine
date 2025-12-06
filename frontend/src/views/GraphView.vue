<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, computed } from 'vue'
import * as d3 from 'd3'
import { useNeo4jStore, type GraphNode, type GraphLink, type Neo4jMessage } from '@/stores/neo4jStore'
import { useStoryStore } from '@/stores/storyStore'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

import { Slider } from '@/components/ui/slider'

import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'


const store = useNeo4jStore()
const storyStore = useStoryStore()
const containerRef = ref<HTMLElement | null>(null)

// --- Chat Variables ---
const chatMessages = ref<Neo4jMessage[]>([])
const chatInput = ref('')
const isChatLoading = ref(false)

async function handleSendMessage() {
  if (!chatInput.value.trim()) return
  
  const userMsg: Neo4jMessage = { sender: 'user', content: chatInput.value }
  chatMessages.value.push(userMsg)
  const query = chatInput.value
  chatInput.value = ''
  
  isChatLoading.value = true
  try {
    const response = await store.naturalLanguageQuery(query)
    if (typeof response === 'string') {
      chatMessages.value.push({ sender: 'assistant', content: response })
    } else {
      chatMessages.value.push({ sender: 'assistant', content: 'Sorry, there was an error generating the response.' })
    }
  } catch (e) {
    console.error(e)
    chatMessages.value.push({ sender: 'assistant', content: 'Error processing request.' })
  } finally {
    isChatLoading.value = false
  }
}

// --- D3 Variables ---
let simulation: d3.Simulation<GraphNode, GraphLink> | null = null
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
let g: d3.Selection<SVGGElement, unknown, null, undefined>

// --- Configuration ---
const NODE_RADIUS = 25
const LINK_LENGTH = ref(180)
const linkLengthArray = computed({
  get: () => [LINK_LENGTH.value],
  set: (val) => {
    const v = val?.[0]
    if (typeof v === 'number') {
      LINK_LENGTH.value = v
    }
  }
})

const currentStoryName = ref<string>("Select Story")

watch(currentStoryName, () => {
  chatMessages.value = []
})

async function selectStory(story: any) {
  currentStoryName.value = story.title
  await store.fetchGraphData(story.neo_database_name)
}

const selectedLinksGroup = computed(() => {
  if (!store.selectedLink) return []
  const sId = getId(store.selectedLink.source)
  const tId = getId(store.selectedLink.target)
  
  return store.links.filter(l => {
    const lsId = getId(l.source)
    const ltId = getId(l.target)
    return (lsId === sId && ltId === tId) || (lsId === tId && ltId === sId)
  })
})

onMounted(async () => {
  if (containerRef.value) {
    initGraph()
    await storyStore.fetchAllStories()
    if (storyStore.stories.length > 0) {
      selectStory(storyStore.stories[0])
    }
  }
})

onUnmounted(() => {
  if (simulation) simulation.stop()
})

watch(() => LINK_LENGTH.value, () => {
  updateGraph()
})

watch(() => store.nodes, () => {
  updateGraph()
})

watch(() => store.selectedNode, async (newNode) => {
  if (newNode) {
    const label = newNode.labels[0] || ''
    const name = newNode.properties.id
    await store.fetchMentionedChapters(label, name)
  } else {
    store.chaptersForSelectedNode = []
  }
})

// --- DYNAMIC COLOR GENERATOR ---
// This ensures that "Person" is always the same color, but we don't hardcode "Person".
function getLabelColor(label: string, opacity: number = 1): string {
  if (!label) return `rgba(156, 163, 175, ${opacity})` // Gray fallback

  let hash = 0;
  for (let i = 0; i < label.length; i++) {
    hash = label.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const h = Math.abs(hash % 360);
  return `hsla(${h}, 65%, 45%, ${opacity})`;
}

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
  
  svg.call(zoom).on('dblclick.zoom', null)

  // Arrow marker
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
    .force('link', d3.forceLink<GraphNode, GraphLink>().id(d => d.id).distance(LINK_LENGTH.value))
    .force('charge', d3.forceManyBody().strength(-500))
    .force('collide', d3.forceCollide(NODE_RADIUS + 10))
    .force('center', d3.forceCenter(width / 2, height / 2))
}

function updateGraph() {
  if (!simulation) return

  // Calculate link groups for curvature
  const linkGroups = new Map<string, GraphLink[]>();
  store.links.forEach(l => {
      const sId = typeof l.source === 'object' ? (l.source as GraphNode).id : l.source;
      const tId = typeof l.target === 'object' ? (l.target as GraphNode).id : l.target;
      const key = sId < tId ? `${sId}-${tId}` : `${tId}-${sId}`;
      if (!linkGroups.has(key)) linkGroups.set(key, []);
      linkGroups.get(key)!.push(l);
  });
  
  linkGroups.forEach(group => {
      group.forEach((l, i) => {
          (l as any).linkIndex = i;
          (l as any).totalLinks = group.length;
      });
  });

  // 1. Links
  const link = g.selectAll<SVGPathElement, GraphLink>('.link')
    .data(store.links, d => d.id)
    .join('path')
    .attr('class', 'link')
    .attr('stroke', '#cbd5e1')
    .attr('stroke-width', 2)
    .attr('marker-end', 'url(#arrow)')
    .attr('fill', 'none')
    .style('cursor', 'pointer')
    .on('click', (e, d) => {
      e.stopPropagation()
      store.selectedLink = d
      store.selectedNode = null
    })

  // 2. Link Labels (Background + Text for readability)
  const linkLabelGroup = g.selectAll<SVGGElement, GraphLink>('.link-label-group')
    .data(store.links, d => d.id)
    .join('g')
    .attr('class', 'link-label-group')
    .style('pointer-events', 'none')


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

  // Node Circle
  node.selectAll('circle')
    .data(d => [d])
    .join('circle')
    .attr('r', NODE_RADIUS)
    .attr('fill', d => {
       // Use our new dynamic function
       const label = d.labels[0] || 'Unknown';
       return getLabelColor(label);
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'grab')
    .style('filter', 'drop-shadow(0 2px 4px rgb(0 0 0 / 0.1))')

  // Node Icon/Text
  node.selectAll('.node-initials')
    .data(d => [d])
    .join('text')
    .attr('class', 'node-initials')
    .text(d => d.properties.id.substring(0, 2).toUpperCase())
    .attr('text-anchor', 'middle')
    .attr('dy', 4)
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('fill', 'white') 
    .style('pointer-events', 'none')
    .style('text-shadow', '0px 1px 2px rgba(0,0,0,0.3)')

  // Label Below
  node.selectAll('.node-label')
    .data(d => [d])
    .join('text')
    .attr('class', 'node-label')
    .text(d => d.properties.id)
    .attr('text-anchor', 'middle')
    .attr('dy', NODE_RADIUS + 14)
    .style('font-size', '11px')
    .style('fill', '#475569')
    .style('pointer-events', 'none')
    .style('text-shadow', '1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff')

  simulation.nodes(store.nodes).on('tick', () => {
    link.attr('d', d => {
        const source = d.source as GraphNode;
        const target = d.target as GraphNode;
        
        const dx = target.x! - source.x!;
        const dy = target.y! - source.y!;
        
        const linkIndex = (d as any).linkIndex || 0;
        const totalLinks = (d as any).totalLinks || 1;

        if (totalLinks > 1) {
             const midX = (source.x! + target.x!) / 2;
             const midY = (source.y! + target.y!) / 2;
             
             let nx = -dy;
             let ny = dx;
             const len = Math.sqrt(nx*nx + ny*ny) || 1;
             nx /= len;
             ny /= len;
             
             const spacing = 30; 
             const offset = (linkIndex - (totalLinks - 1) / 2) * spacing;
             
             const cx = midX + nx * offset;
             const cy = midY + ny * offset;
             
             return `M${source.x},${source.y}Q${cx},${cy} ${target.x},${target.y}`;
        } else {
             return `M${source.x},${source.y}L${target.x},${target.y}`;
        }
    })

    // Update label group position (calculated center)
    linkLabelGroup
      .attr('transform', d => {
        const source = d.source as GraphNode;
        const target = d.target as GraphNode;
        
        const linkIndex = (d as any).linkIndex || 0;
        const totalLinks = (d as any).totalLinks || 1;

        if (totalLinks > 1) {
             const dx = target.x! - source.x!;
             const dy = target.y! - source.y!;
             const midX = (source.x! + target.x!) / 2;
             const midY = (source.y! + target.y!) / 2;
             let nx = -dy;
             let ny = dx;
             const len = Math.sqrt(nx*nx + ny*ny) || 1;
             nx /= len;
             ny /= len;
             const spacing = 30;
             const offset = (linkIndex - (totalLinks - 1) / 2) * spacing;
             const cx = midX + nx * offset;
             const cy = midY + ny * offset;
             
             const x = (source.x! + 2*cx + target.x!) / 4;
             const y = (source.y! + 2*cy + target.y!) / 4;
             return `translate(${x},${y})`;
        } else {
             const x = (source.x! + target.x!) / 2;
             const y = (source.y! + target.y!) / 2;
             return `translate(${x},${y})`;
        }
      })

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  simulation.force('collide', d3.forceCollide(NODE_RADIUS + 10))
  simulation.force<d3.ForceLink<GraphNode, GraphLink>>('link')!.links(store.links).distance(LINK_LENGTH.value)
  simulation.alpha(1).restart()
}

function clearSelection() {
  store.selectedNode = null
  store.selectedLink = null
}

function getId(node: string | GraphNode): string {
  return typeof node === 'string' ? node : node.id
}

function filterProps(props: Record<string, any>) {
  const { id, ...rest } = props
  return rest
}

function highlightText(text: string, term: string | undefined) {
  if (!term || !text) return text
  // Escape special regex characters in the term just in case
  const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escapedTerm})`, 'gi')
  return text.replace(regex, '<span class="bg-yellow-200 font-semibold text-slate-900 px-0.5 rounded">$1</span>')
}

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

<template>

  <ResizablePanelGroup 
    direction="horizontal" 
    class="h-[800px] w-full border rounded-xl bg-slate-50 overflow-hidden shadow-sm font-sans"
  >
    <ResizablePanel :default-size="store.selectedNode ? 70 : 100" :min-size="30">
      <ResizablePanelGroup direction="vertical">
        <ResizablePanel :default-size="60" :min-size="30" class="relative">
      
      <!-- Story Selector -->
      <div class="absolute top-4 left-4 z-10">
        <DropdownMenu>
          <DropdownMenuTrigger class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium py-2 px-4 rounded-lg shadow-sm flex items-center gap-2 transition-colors outline-none focus:ring-2 focus:ring-slate-200">
            <span>{{ currentStoryName }}</span>
            <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-56 bg-white" align="start">
            <DropdownMenuLabel>Available Stories</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem v-for="story in storyStore.stories" :key="story.id" @click="selectStory(story)">
              {{ story.title }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <!-- Link length slider -->
        <div class="mt-2 w-40 bg-white border border-slate-200 rounded-lg shadow-sm p-3">
          <label class="block text-xs font-medium text-slate-600 mb-1">Link Length</label>
          <Slider v-model="linkLengthArray" :min="50" :max="300" :step="1" />
        </div>

      </div>

      

      

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
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
          </div>

          <div class="p-4 space-y-4">
            
            <!-- Node Content -->
            <div v-if="store.selectedNode">
              <div class="mb-4">
                 <h2 class="text-xl font-bold text-slate-900 leading-tight">
                   {{ store.selectedNode.properties.id }}
                 </h2>
                 <div class="flex flex-wrap gap-1 mt-2">
                  <span v-for="label in store.selectedNode.labels" :key="label"
                        :style="{ backgroundColor: getLabelColor(label, 0.15), color: getLabelColor(label, 1.0), borderColor: getLabelColor(label, 0.3) }"
                        class="px-2.5 py-0.5 text-xs font-bold rounded-full border">
                    {{ label }}
                  </span>
                </div>
              </div>

              <div v-if="store.selectedNode.properties.description" class="bg-slate-50 p-3 rounded-md border border-slate-100 text-sm text-slate-600 italic mb-4">
                "{{ store.selectedNode.properties.description }}"
              </div>

              <div class="space-y-3">
                <div v-for="(val, key) in filterProps(store.selectedNode.properties)" :key="key" class="text-sm group">
                  <span class="text-xs font-bold text-slate-400 uppercase block mb-0.5">{{ key }}</span>
                  <span class="text-slate-700 break-words leading-relaxed block bg-slate-50 px-2 py-1 rounded border border-slate-100">{{ val }}</span>
                </div>
              </div>
            </div>

            <!-- Link Content -->
            <div v-if="store.selectedLink">
               <div v-for="(link, idx) in selectedLinksGroup" :key="link.id" class="mb-4 border-b pb-4 last:border-0 last:pb-0 last:mb-0">
                   <div class="text-center py-2 bg-slate-50 rounded border border-slate-100 mb-2">
                     <span class="text-xs font-bold text-slate-400 block mb-1">TYPE</span>
                     <span class="text-lg font-mono font-bold text-slate-700">{{ link.type }}</span>
                   </div>
                   
                   <div class="text-xs text-slate-500 text-center">
                     Connected <br/>
                     <span class="font-semibold text-slate-700">{{ getId(link.source) }}</span>
                     <span class="mx-1">→</span>
                     <span class="font-semibold text-slate-700">{{ getId(link.target) }}</span>
                   </div>
               </div>
            </div>

          </div>
        </div>
      </transition>
        </ResizablePanel>

        <ResizableHandle />

        <ResizablePanel :default-size="40" :min-size="10">
          <!-- Chat Component -->
          <Card class="flex flex-col shadow-xl h-full w-full overflow-hidden bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
          <CardHeader class="p-3 border-b bg-slate-50/50">
            <CardTitle class="text-sm font-medium flex items-center gap-2 text-slate-700">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
              Chat with the Graph
            </CardTitle>
          </CardHeader>
          <CardContent class="flex-1 p-0 overflow-hidden relative">
            <ScrollArea class="h-full w-full p-4">
              <div v-if="chatMessages.length === 0" class="text-center text-slate-400 text-sm mt-4 italic">
                Ask a question about the graph...
              </div>
              <div v-for="(msg, i) in chatMessages" :key="i" class="mb-4 text-sm">
                <div :class="['font-bold mb-1 text-xs uppercase tracking-wide', msg.sender === 'user' ? 'text-blue-600' : 'text-slate-500']">
                  {{ msg.sender === 'user' ? 'You' : 'Assistant' }}
                </div>
                <div class="text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 p-2 rounded border border-slate-100">{{ msg.content }}</div>
              </div>
              <div v-if="isChatLoading" class="flex items-center gap-2 text-xs text-slate-400 italic mt-2">
                <div class="h-2 w-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div class="h-2 w-2 bg-slate-400 rounded-full animate-bounce delay-75"></div>
                <div class="h-2 w-2 bg-slate-400 rounded-full animate-bounce delay-150"></div>
                Thinking...
              </div>
            </ScrollArea>
          </CardContent>
          <CardFooter class="p-3 border-t bg-slate-50">
            <form @submit.prevent="handleSendMessage" class="flex w-full gap-2">
              <Input v-model="chatInput" placeholder="Ask about the story..." class="h-8 text-sm bg-white" />
              <Button type="submit" size="sm" class="h-8 px-3" :disabled="isChatLoading">
                Send
              </Button>
            </form>
          </CardFooter>
          </Card>
        </ResizablePanel>
      </ResizablePanelGroup>
    </ResizablePanel>

    <ResizableHandle v-if="store.selectedNode" />
      <!-- Mentioned Chapter Container -->
    <ResizablePanel v-if="store.selectedNode" :default-size="30" :min-size="20">
      <div class="h-full overflow-y-auto bg-white border-l border-slate-200 p-4">
        <Card class="border-0 shadow-none">
          <CardTitle class="mb-4">Chapters Mentioning "{{ store.selectedNode.properties.id }}"</CardTitle>
          <CardContent v-if="store.areChaptersLoading" class="flex flex-col items-center justify-center h-48">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-800 border-t-transparent"></div>
            <span class="mt-2 text-sm font-medium text-slate-600">Loading Chapters...</span>
          </CardContent>
          <CardContent v-else-if="store.chaptersForSelectedNode && store.chaptersForSelectedNode.length === 0" class="text-sm text-slate-500 italic">
            No chapters found mentioning this entity.
          </CardContent>
          <CardContent v-else class="p-0">
            <Accordion type="single" collapsible class="w-full">
              <AccordionItem v-for="(chapter, index) in store.chaptersForSelectedNode || []" :key="index" :value="`item-${index}`">
                <AccordionTrigger class="px-4 hover:no-underline hover:bg-slate-50">
                  <span class="font-semibold text-slate-800 text-left">{{ chapter.title }}</span>
                </AccordionTrigger>
                <AccordionContent class="px-4 pb-4 text-slate-600">
                  <p v-html="highlightText(chapter.content, store.selectedNode?.properties.id)" class="whitespace-pre-wrap"></p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </div>
    </ResizablePanel>

  </ResizablePanelGroup>
</template>