<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useStoryStore } from '@/stores/storyStore'
import type { CreateStoryPayload } from '@/stores/storyStore'

const router = useRouter()
const storyStore = useStoryStore()

const fullText = "Welcome to TaleMachine!"
const displayedText = ref("")

const typeWriter = async () => {
  for (let i = 0; i < fullText.length; i++) {
    displayedText.value += fullText.charAt(i)
    await new Promise(resolve => setTimeout(resolve, 50))
  }
}

onMounted(() => {
  typeWriter()
})

const storyName = ref('')
const storyLength = ref<CreateStoryPayload['story_length']>('medium')
const chapterLength = ref<CreateStoryPayload['chapter_length']>('medium')
const genre = ref<CreateStoryPayload['genre']>('fantasy')
const additionalNotes = ref('')
const mainCharacters = ref('')
const plotIdeas = ref('')

const isDialogOpen = ref(false)
const isCreating = ref(false)

const createStoryAndStart = async () => {
  if (!storyName.value.trim()) return
  
  isCreating.value = true
  try {    
    const payload: CreateStoryPayload = {
      title: storyName.value,
      story_length: storyLength.value,
      chapter_length: chapterLength.value,
      genre: genre.value,
      additional_notes: additionalNotes.value || null,
      main_characters: mainCharacters.value || null,
      plot_ideas: plotIdeas.value || null
    }

    const newStory = await storyStore.createStory(payload)
    
    if (newStory) {
      // Set current story
      await storyStore.fetchStory(newStory.id)
      
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
    <h1 class="text-4xl md:text-6xl font-bold text-center bg-linear-to-r from-chart-3 to-chart-2 bg-clip-text text-transparent min-h-[1.5em]">
      {{ displayedText }}
    </h1>
    <Accordion type="single" collapsible class="w-full max-w-2xl mb-8">
      <AccordionItem value="how-it-works">
        <AccordionTrigger><span class="how-it-works-title">How it works</span></AccordionTrigger>
        <AccordionContent>
          <p class="whitespace-pre-wrap text-muted-foreground mb-4">
            To start writing, simply give the AI a quick overview of your story, including the title, genre, and key characters to set the context. You can then collaborate with the AI to draft new chapters or edit specific scenes. Since the chat acts as a temporary workspace for creativity, remember to explicitly tell the AI to save your chapter once you are satisfied. This permanently stores your progress, allowing you to pick up exactly where you left off later.
          </p>
          <p class="whitespace-pre-wrap text-muted-foreground">
            As your story grows, TaleMachine helps you keep track of your world. You can visit the Graph tab to see a visual map of how your characters and locations connect, ensuring your lore stays consistent. You can also bring your narrative to life by asking the AI to generate illustrations for your scenes, which can be linked directly to your chapters or saved to your gallery.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
    <Button
      variant = "default"
      size = "lg"
      class="mb-6 cursor-pointer"
      @click="isDialogOpen = true"
    >Create New Story</Button>

    <Dialog v-model:open="isDialogOpen">
      <DialogContent class="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create your Story</DialogTitle>
          <DialogDescription>
            Configure the details of your new adventure.
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid gap-2">
            <Label for="name">Story Title</Label>
            <Input 
              id="name"
              v-model="storyName" 
              placeholder="Enter story name..." 
              autoFocus
            />
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div class="grid gap-2">
              <Label>Story Length</Label>
              <Select v-model="storyLength">
                <SelectTrigger>
                  <SelectValue placeholder="Select length" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="short">Short</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="long">Long</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label>Chapter Length</Label>
              <Select v-model="chapterLength">
                <SelectTrigger>
                  <SelectValue placeholder="Select length" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="short">Short</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="long">Long</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="grid gap-2">
            <Label>Genre</Label>
            <Select v-model="genre">
              <SelectTrigger>
                <SelectValue placeholder="Select genre" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Fiction</SelectLabel>
                  <SelectItem value="fantasy">Fantasy</SelectItem>
                  <SelectItem value="sci-fi">Sci-Fi</SelectItem>
                  <SelectItem value="mystery">Mystery</SelectItem>
                  <SelectItem value="thriller">Thriller</SelectItem>
                  <SelectItem value="romance">Romance</SelectItem>
                  <SelectItem value="young_adult">Young Adult</SelectItem>
                  <SelectItem value="children">Children</SelectItem>
                  <SelectItem value="historical">Historical</SelectItem>
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Other</SelectLabel>
                  <SelectItem value="action">Action</SelectItem>
                  <SelectItem value="drama">Drama</SelectItem>
                  <SelectItem value="comedy">Comedy</SelectItem>
                  <SelectItem value="memoir">Memoir</SelectItem>
                  <SelectItem value="poetry">Poetry</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div class="grid gap-2">
            <Label for="plot">Plot Ideas</Label>
            <Textarea 
              id="plot" 
              v-model="plotIdeas" 
              placeholder="Describe the plot or starting scenario..." 
              class="h-20"
            />
          </div>

          <div class="grid gap-2">
            <Label for="characters">Main Characters</Label>
            <Textarea 
              id="characters" 
              v-model="mainCharacters" 
              placeholder="List main characters and their traits..." 
              class="h-20"
            />
          </div>

          <div class="grid gap-2">
            <Label for="notes">Additional Notes</Label>
            <Textarea 
              id="notes" 
              v-model="additionalNotes" 
              placeholder="Any other details or instructions..." 
              class="h-20"
            />
          </div>
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
.how-it-works-title {
  font-weight: lighter;
  font-size: 1.25rem;
}
</style>
