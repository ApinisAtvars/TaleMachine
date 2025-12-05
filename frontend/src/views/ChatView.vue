<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { ArrowUpIcon, UserIcon, BotIcon, ChevronDownIcon, ImageIcon, XIcon, BookMarked } from 'lucide-vue-next'
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from '@/components/ui/input-group'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'

import { useStoryStore} from '@/stores/storyStore'

const props = defineProps<{
  storyId: string
}>()


const storyStore = useStoryStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const selectedChapterId = ref<number | null>(null)
const isImageGalleryOpen = ref(false)
const isChapterSidebarOpen = ref(false)
const selectedImage = ref<string | null>(null)

const isAnySidebarOpen = computed(() => isChapterSidebarOpen.value || isImageGalleryOpen.value)

const selectedChapterName = computed(() => {
  if (selectedChapterId.value === null) return 'Save to story'
  const chapter = storyStore.currentChapters.find(c => c.id === selectedChapterId.value)
  return chapter ? chapter.title : 'Save to story'
})

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleSend = async () => {
  const content = messageInput.value.trim()
  if (!content) return

  messageInput.value = ''
  await storyStore.sendMessage(content)
}

const handleApproval = async (approved: boolean) => {
  await storyStore.resumeAfterInterrupt(approved, null)
}

const handleImageGenApproval = async (approved: boolean, chapterId: number | null) => {
  await storyStore.resumeAfterInterrupt(approved, chapterId)
  await storyStore.fetchImages(storyStore.currentStory!.id)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

onMounted(async () => {
  const id = parseInt(props.storyId)
  if (!isNaN(id)) {
    if (!storyStore.currentStory || storyStore.currentStory.id !== id) {
      await storyStore.fetchStory(id)
    }
  }
  scrollToBottom()
})

watch(
  () => storyStore.messages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)

watch(
  () => props.storyId,
  async (newId) => {
    const id = parseInt(newId)
    if (!isNaN(id)) {
      await storyStore.fetchStory(id)
    }
  }
)
</script>

<template>
  <div class="h-full relative overflow-hidden">
    <ResizablePanelGroup direction="horizontal" class="h-full items-stretch">
      <ResizablePanel :default-size="100" :min-size="30">
        <div class="flex flex-col h-full min-w-0 relative">
    <!-- Messages Area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-6">
      <div v-if="storyStore.loading && !storyStore.messages.length" class="flex justify-center items-center h-full text-muted-foreground">
        Loading story...
      </div>
      
      <div v-else-if="!storyStore.messages.length" class="flex justify-center items-center h-full text-muted-foreground">
        No messages yet. Start the conversation!
      </div>

      <div
        v-for="(message, index) in storyStore.messages"
        :key="index"
        class="flex gap-4 max-w-3xl mx-auto"
        :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- Avatar for Assistant -->
        <div v-if="message.role === 'assistant'" class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <BotIcon class="w-5 h-5 text-primary" />
        </div>

        <!-- Message Content -->
        <div
          class="rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap"
          
          :class="[
            message.role === 'user' 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted text-foreground'
          ]"
        >
          <div v-if="message.title" class="font-bold mb-1 text-center text-3xl">{{ message.title }}</div>
          <Separator v-if="message.title" class="my-5" />
          {{ message.content }}
        </div>

        <!-- Avatar for User -->
        <div v-if="message.role === 'user'" class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
          <UserIcon class="w-5 h-5 text-secondary-foreground" />
        </div>
      </div>
      
      <!-- Loading/Streaming Indicator -->
      <div v-if="storyStore.streaming && storyStore.messages[storyStore.messages.length - 1]?.role === 'user'" class="flex gap-4 max-w-3xl mx-auto">
         <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <BotIcon class="w-5 h-5 text-primary" />
        </div>
        <div class="bg-muted text-foreground rounded-lg px-4 py-2">
          <span class="animate-pulse">...</span>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="p-4 bg-background">
      <div class="max-w-3xl mx-auto">
        <InputGroup>
          <InputGroupTextarea 
            v-model="messageInput"
            placeholder="Type your message..." 
            @keydown="handleKeydown"
            class="min-h-[3rem] max-h-[10rem]"
          />
          <InputGroupAddon align="inline-end">
            <InputGroupButton
              variant="default"
              class="rounded-full"
              size="icon-xs"
              :disabled="!messageInput.trim() || storyStore.streaming"
              @click="handleSend"
              v-if="!storyStore.loading && !storyStore.streaming"
            >
              <ArrowUpIcon class="size-4" />
              <span class="sr-only">Send</span>
            </InputGroupButton>
            <Spinner v-else class="size-5 text-primary" />
          </InputGroupAddon>
        </InputGroup>
        <div class="text-xs text-muted-foreground text-center mt-2">
          Press Enter to send, Shift + Enter for new line
        </div>
      </div>
    </div>

    <!-- Toggle Buttons for Image Gallery and Story Chapters -->
    <Button 
      v-if="!isImageGalleryOpen && !isChapterSidebarOpen"
      variant="outline" 
      size="icon" 
      class="absolute top-4 right-4 z-10 bg-background/80 backdrop-blur-sm shadow-sm hover:bg-background"
      @click="isImageGalleryOpen = true"
      title="Show Images"
    >
      <ImageIcon class="w-4 h-4" />
    </Button>
    <Button
      v-if="!isChapterSidebarOpen && !isImageGalleryOpen"
      variant="outline" 
      size="icon" 
      class="absolute top-16 right-4 z-10 bg-background/80 backdrop-blur-sm shadow-sm hover:bg-background"
      @click="isChapterSidebarOpen = true"
      title="Show Chapters"
    >
      <BookMarked class="w-4 h-4" />
    </Button>
    </div>
      </ResizablePanel>

      <ResizableHandle v-if="isAnySidebarOpen" with-handle />

      <ResizablePanel v-if="isAnySidebarOpen" :default-size="25" :min-size="20" :max-size="50">
        <!-- Right Card (Chapter Sidebar) -->
        <Card 
          v-if="isChapterSidebarOpen"
          class="bg-background flex flex-col h-full overflow-hidden border-0 rounded-none"
        >
          <CardHeader class="border-b flex justify-between items-center shrink-0">
                <CardTitle>Story Chapter Viewer</CardTitle>
                <Button variant="ghost" size="icon" @click="isChapterSidebarOpen = false">
                    <XIcon class="w-4 h-4" />
                </Button>
            </CardHeader>
            
            <CardContent class="flex-1 min-h-0">
              <ScrollArea class="h-full">
                  <div v-if="storyStore.currentChapters.length === 0" class="text-center text-muted-foreground py-8">
                      No chapters generated yet.
                  </div>
                  <div v-else class="grid grid-cols-1 gap-4">
                      <div v-for="chapter in storyStore.currentChapters" :key="chapter.id" class="space-y-2">
                          <div class="p-4">
                              <h3 class="font-bold text-lg mb-2">{{ chapter.title }}</h3>
                              <p class="text-sm text-foreground/80">{{ chapter.content }}</p>
                          </div>
                      </div>
                  </div>
              </ScrollArea>
            </CardContent>
        </Card>
        <!-- Right Card (Image Gallery) -->
        <Card 
          v-if="isImageGalleryOpen"
          class="bg-background flex flex-col h-full overflow-hidden border-0 rounded-none"
        >
            <CardHeader class="border-b flex justify-between items-center shrink-0">
                <CardTitle>Story Image Gallery</CardTitle>
                <Button variant="ghost" size="icon" @click="isImageGalleryOpen = false">
                    <XIcon class="w-4 h-4" />
                </Button>
            </CardHeader>
            
            <CardContent class="flex-1 min-h-0">
              <ScrollArea class="h-full">
                  <div v-if="storyStore.currentImages.length === 0" class="text-center text-muted-foreground py-8">
                      No images generated yet.
                  </div>
                  <div v-else class="grid grid-cols-1 gap-4">
                      <div v-for="image in storyStore.currentImages" :key="image.id" class="space-y-2">
                          <div class="aspect-square rounded-md overflow-hidden border bg-muted relative group">
                              <img 
                                  v-if="image.link" 
                                  :src="image.link" 
                                  class="object-cover w-full h-full transition-transform duration-300 group-hover:scale-105" 
                                  loading="lazy"
                              />
                              <div v-else class="flex items-center justify-center h-full text-muted-foreground">
                                  <ImageIcon class="w-8 h-8 opacity-20" />
                              </div>
                              
                              <div 
                                  v-if="image.link"
                                  @click="selectedImage = image.link"
                                  class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer"
                              >
                              </div>
                          </div>
                      </div>
                  </div>
              </ScrollArea>
            </CardContent>
          </Card>
      </ResizablePanel>
    </ResizablePanelGroup>

    <!-- Image Preview Dialog -->
    <Dialog :open="!!selectedImage" @update:open="(val) => !val && (selectedImage = null)">
      <DialogContent class="w-fit h-fit p-0 overflow-hidden bg-transparent border-none shadow-none flex items-center justify-center">
             <img 
              v-if="selectedImage" 
              :src="selectedImage" 
              class="object-contain rounded-md shadow-lg"
              alt="Full size preview"
            />
      </DialogContent>
    </Dialog>

    <!-- Interrupt Dialog -->
    <Dialog :open="storyStore.interruptTriggered && !storyStore.imageGenInterruptTriggered">
      <DialogContent :show-close-button="false" @pointer-down-outside.prevent @escape-key-down.prevent>
        <DialogHeader>
          <DialogTitle>Permission Request</DialogTitle>
          <DialogDescription>
            <ScrollArea class="h-[300px] w-full rounded-md border p-4">
              {{ storyStore.interruptMessage || 'The AI needs your approval to proceed.' }}
            </ScrollArea>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="handleApproval(false)">Deny</Button>
          <Button @click="handleApproval(true)">Approve</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    <!-- Image Generation Interrupt Dialog -->
    <Dialog :open="storyStore.imageGenInterruptTriggered">
      <DialogContent :show-close-button="false" @pointer-down-outside.prevent @escape-key-down.prevent>
        <DialogHeader>
          <DialogTitle>Image Generation Approval</DialogTitle>
          <DialogDescription>
            The AI wants to generate an image. Please select a chapter to associate it with, or save it to the story generally.
          </DialogDescription>
        </DialogHeader>
        
        <div class="py-4">
            <DropdownMenu>
                <DropdownMenuTrigger as-child>
                    <Button variant="outline" class="w-full justify-between">
                        {{ selectedChapterName }}
                        <ChevronDownIcon class="ml-2 h-4 w-4" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent class="w-56">
                    <DropdownMenuLabel>Select Chapter</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem @click="selectedChapterId = null">
                        Save to story
                    </DropdownMenuItem>
                    <DropdownMenuItem v-for="chapter in storyStore.currentChapters" :key="chapter.id" @click="selectedChapterId = chapter.id">
                        {{ chapter.title }}
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="handleImageGenApproval(false, null)">Deny</Button>
          <Button @click="handleImageGenApproval(true, selectedChapterId)">Approve</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
</style>
