<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowUpIcon } from 'lucide-vue-next'
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
import { Input } from '@/components/ui/input'
import { useStoryStore } from '@/stores/storyStore'

const router = useRouter()
const storyStore = useStoryStore()

const initialMessage = ref('')
const storyName = ref('')
const isDialogOpen = ref(false)
const isCreating = ref(false)

const handleInitialSend = () => {
  if (!initialMessage.value.trim()) return
  isDialogOpen.value = true
}

const createStoryAndStart = async () => {
  if (!storyName.value.trim()) return
  
  isCreating.value = true
  try {
    // Generate a simple db name from title or random
    const neoDbName = storyName.value.toLowerCase().replace(/[^a-z0-9]/g, '_') + '_' + Date.now()
    
    const newStory = await storyStore.createStory(storyName.value, neoDbName)
    
    if (newStory) {
      // Set current story
      await storyStore.fetchStory(newStory.id)
      
      // Send the initial message
      await storyStore.sendMessage(initialMessage.value)
      
      // Navigate to chat
      router.push({ name: 'chat', params: { storyId: newStory.id } })
    }
  } catch (error) {
    console.error('Failed to create story:', error)
  } finally {
    isCreating.value = false
    isDialogOpen.value = false
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] px-4">
    <h1 class="text-4xl md:text-6xl font-bold text-center mb-8 bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
      Welcome to TaleMachine!
    </h1>
    
    <div class="w-full max-w-2xl">
      <InputGroup>
        <InputGroupTextarea 
          v-model="initialMessage" 
          placeholder="Ask, Search or Chat..." 
          @keydown.enter.prevent="handleInitialSend"
        />
        <InputGroupAddon align="block-end">
          <InputGroupButton
            variant="default"
            class="rounded-full"
            size="icon-xs"
            :disabled="!initialMessage.trim()"
            @click="handleInitialSend"
          >
            <ArrowUpIcon class="size-4" />
            <span class="sr-only">Send</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </div>

    <Dialog v-model:open="isDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Name your Story</DialogTitle>
          <DialogDescription>
            Give your new adventure a title to get started.
          </DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <Input 
            v-model="storyName" 
            placeholder="Enter story name..." 
            @keydown.enter="createStoryAndStart"
            autoFocus
          />
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isDialogOpen = false">Cancel</Button>
          <Button @click="createStoryAndStart" :disabled="isCreating || !storyName.trim()">
            {{ isCreating ? 'Creating...' : 'Start Adventure' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
</style>
