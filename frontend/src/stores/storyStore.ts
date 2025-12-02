import { defineStore } from 'pinia'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

// --- Types based on Database Schema ---

export interface Story {
  id: number
  title: string
  neo_database_name: string
}

export interface Image {
  id: number
  image_path: string
  story_id: number
}

export interface Chapter {
  id: number
  content: string
  timestamp: number
  story_id: number
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface State {
  // Data
  stories: Story[]
  currentStory: Story | null
  currentImages: Image[]
  currentChapters: Chapter[]
  
  // Chat / Interaction
  messages: Message[]
  threadId: string
  
  // UI States
  loading: boolean
  streaming: boolean
  error: string | null
  
  // Interrupt Handling
  interruptTriggered: boolean
  interruptMessage: string // The content after "__interrupt__:"
}

// Base API URL
const API_URL = 'http://localhost:8000' // Adjust to your backend URL

export const useStoryStore = defineStore('story', {
  state: (): State => ({
    stories: [],
    currentStory: null,
    currentImages: [],
    currentChapters: [],
    messages: [],
    threadId: uuidv4(), // Generate a random thread ID on init
    loading: false,
    streaming: false,
    error: null,
    interruptTriggered: false,
    interruptMessage: '',
  }),

  getters: {
    getStoryById: (state) => (id: number) => state.stories.find((s) => s.id === id),
  },

  actions: {
    // =========================================
    // STORY ENDPOINTS
    // =========================================

    // GET /story/all
    async fetchAllStories() {
      this.loading = true
      try {
        const response = await axios.get(`${API_URL}/story/all`)
        this.stories = response.data
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    // GET /story/find/{story_id}
    async fetchStory(storyId: number) {
      this.loading = true
      try {
        const response = await axios.get(`${API_URL}/story/find/${storyId}`)
        this.currentStory = response.data
        // When selecting a story, we also fetch its related assets
        await Promise.all([
            this.fetchImages(storyId),
            this.fetchChapters(storyId)
        ])
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    // POST /story/insert
    async createStory(title: string, neoDatabaseName: string) {
      try {
        const payload = { title, neo_database_name: neoDatabaseName }
        const response = await axios.post(`${API_URL}/story/insert`, payload)
        this.stories.push(response.data)
        return response.data
      } catch (err: any) {
        this.error = err.message
      }
    },

    // POST /story/update
    async updateStoryTitle(storyId: number, newTitle: string) {
      try {
        const payload = { id: storyId, title: newTitle }
        await axios.post(`${API_URL}/story/update`, payload)
        
        // Update local state
        const story = this.stories.find(s => s.id === storyId)
        if (story) story.title = newTitle
        if (this.currentStory?.id === storyId) this.currentStory.title = newTitle
        
      } catch (err: any) {
        this.error = err.message
      }
    },

    // DELETE /story/{story_id}
    async deleteStory(storyId: number) {
      try {
        await axios.delete(`${API_URL}/story/${storyId}`)
        this.stories = this.stories.filter(s => s.id !== storyId)
        if (this.currentStory?.id === storyId) {
            this.currentStory = null
            this.currentImages = []
            this.currentChapters = []
            this.messages = []
        }
      } catch (err: any) {
        this.error = err.message
      }
    },

    // =========================================
    // IMAGE & CHAPTER ENDPOINTS
    // =========================================

    // GET /images/all/{story_id}
    async fetchImages(storyId: number) {
      try {
        const response = await axios.get(`${API_URL}/images/all/${storyId}`)
        this.currentImages = response.data
      } catch (err: any) {
        this.error = err.message
      }
    },

    // GET /chapter/all/{story_id}
    async fetchChapters(storyId: number) {
      try {
        const response = await axios.get(`${API_URL}/chapter/all/${storyId}`)
        this.currentChapters = response.data
      } catch (err: any) {
        this.error = err.message
      }
    },

    // =========================================
    // MESSAGES ENDPOINTS (Streaming & Interrupts)
    // =========================================

    /**
     * Helper to process the text stream from the backend
     */
    async _processStreamResponse(response: Response) {
      if (!response.body) return

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let done = false

      // Create a new assistant message placeholder
      const messageIndex = this.messages.push({ role: 'assistant', content: '' }) - 1

      while (!done) {
        const { value, done: readerDone } = await reader.read()
        done = readerDone
        
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          
          // Check for interrupt signal as seen in Python code
          if (chunk.includes('__interrupt__:')) {
             const [cleanContent, interruptMsg] = chunk.split('__interrupt__:')
             
             // Append the text before the interrupt tag
             this.messages[messageIndex].content += cleanContent
             
             // Set interrupt state
             this.interruptTriggered = true
             this.interruptMessage = interruptMsg.trim()
             this.streaming = false
             return // Stop reading stream to wait for user input
          }

          this.messages[messageIndex].content += chunk
        }
      }
      this.streaming = false
    },

    // POST /messages/send
    async sendMessage(userContent: string) {
      if (!this.currentStory) {
          this.error = "No story selected"
          return
      }

      // Add user message to state
      this.messages.push({ role: 'user', content: userContent })
      this.streaming = true
      this.interruptTriggered = false
      this.error = null

      try {
        // Prepare Payload based on requirements
        const payload = {
          messages: this.messages, // Sending history context
          story_name: this.currentStory.title,
          thread_id: this.threadId,
          story_id: this.currentStory.id
        }

        // Use fetch for streaming support
        const response = await fetch(`${API_URL}/messages/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (!response.ok) throw new Error(response.statusText)

        await this._processStreamResponse(response)

      } catch (err: any) {
        this.error = err.message
        this.streaming = false
      }
    },

    // POST /messages/resume_after_interrupt
    async resumeAfterInterrupt(userApproval: boolean) {
      if (!this.currentStory) return

      // Reset interrupt state
      this.interruptTriggered = false
      this.interruptMessage = ''
      this.streaming = true

      try {
        const payload = {
            story_name: this.currentStory.title,
            thread_id: this.threadId,
            story_id: this.currentStory.id,
            user_approval: userApproval
        }

        const response = await fetch(`${API_URL}/messages/resume_after_interrupt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })

        if (!response.ok) throw new Error(response.statusText)

        // Resume stream into the existing or new message
        // Usually, we append to the last message if the previous one was cut off,
        // but it's safer to create a continuation chunk or append to the last one.
        // Re-using _processStreamResponse will create a NEW message entry.
        // If you want to merge it, logic inside _processStreamResponse needs tweaking.
        // For now, let's treat the resumption as a continuation block.
        
        await this._processStreamResponse(response)

      } catch (err: any) {
        this.error = err.message
        this.streaming = false
      }
    }
  }
})