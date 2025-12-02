<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowUpIcon, UserIcon, BotIcon } from 'lucide-vue-next'
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
import { useStoryStore } from '@/stores/storyStore'

const props = defineProps<{
  storyId: string
}>()

const route = useRoute()
const storyStore = useStoryStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

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
  await storyStore.resumeAfterInterrupt(approved)
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
  <div class="flex flex-col h-[calc(100vh-4rem)] relative">
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
    <div class="p-4 border-t bg-background">
      <div class="max-w-3xl mx-auto">
        <InputGroup>
          <InputGroupTextarea 
            v-model="messageInput"
            placeholder="Type your message..." 
            @keydown="handleKeydown"
            class="min-h-[3rem] max-h-[10rem]"
          />
          <InputGroupAddon align="block-end">
            <InputGroupButton
              variant="default"
              class="rounded-full"
              size="icon-xs"
              :disabled="!messageInput.trim() || storyStore.streaming"
              @click="handleSend"
            >
              <ArrowUpIcon class="size-4" />
              <span class="sr-only">Send</span>
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
        <div class="text-xs text-muted-foreground text-center mt-2">
          Press Enter to send, Shift + Enter for new line
        </div>
      </div>
    </div>

    <!-- Interrupt Dialog -->
    <Dialog :open="storyStore.interruptTriggered">
      <DialogContent :show-close-button="false" @pointer-down-outside.prevent @escape-key-down.prevent>
        <DialogHeader>
          <DialogTitle>Permission Request</DialogTitle>
          <DialogDescription>
            {{ storyStore.interruptMessage || 'The AI needs your approval to proceed.' }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="handleApproval(false)">Deny</Button>
          <Button @click="handleApproval(true)">Approve</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
</style>
