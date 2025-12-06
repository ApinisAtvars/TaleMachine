import { defineStore } from 'pinia'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

// --- Types based on Database Schema ---

export interface Story {
  id: number
  title: string
  neo_database_name: string
  story_length: string
  chapter_length: string
  genre: string
  additional_notes: string | null
  main_characters: string | null
  plot_ideas: string | null
}

export interface Image {
  id: number
  image_path: string
  story_id: number
  chapter_id: number | null // Nullable if image is not tied to a specific chapter
  link: string | null // URL to access the image (FASTAPI_URL/)
}

export interface Chapter {
  id: number
  title: string
  content: string
  timestamp: number
  story_id: number
}

export interface Message {
  role: 'user' | 'assistant'
  title?: string // Normally, messages shouldn't have titles anymore. Only chapters do.
  content: string
}

export interface InterruptMessage {
  tool_name: string;
  args?: { [key: string]: any };
  message?: string;
}

export interface CreateStoryPayload {
    title: string;
    story_length: "short" | "medium" | "long";
    chapter_length: "short" | "medium" | "long";
    genre: "sci-fi" | "action" | "drama" | "comedy" | "mystery" | "thriller" | "romance" | "young_adult" | "fantasy" | "children" | "memoir" | "historical" | "poetry";
    
    // open fields
    additional_notes?: string | null;
    main_characters?: string | null;
    plot_ideas?: string | null;
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
  savingStory: boolean
  error: string | null
  
  // Interrupt Handling
  interruptTriggered: boolean
  imageGenInterruptTriggered: boolean
  interruptMessage: InterruptMessage | null // The content after "__interrupt__:"
}

// Base API URL
const API_URL = 'http://localhost:7890' // Adjust to your backend URL

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
    imageGenInterruptTriggered: false,
    interruptMessage: null,
    savingStory: false,
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
            this.messages = [], // Clear previous messages
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
    async createStory(createStoryPayload: CreateStoryPayload) {
      // DEPRECATED: Story creation now receives special JSON data
      // try {
      //   // const payload = { title, neo_database_name: neoDatabaseName }
      //   const response = await axios.post(`${API_URL}/story/insert?title=${title}&neo_database_name=${neoDatabaseName}`)
      //   this.stories.push(response.data)
      //   return response.data
      // } catch (err: any) {
      //   this.error = err.message
      // }
      try {
        const response = await axios.post(`${API_URL}/story/start_form`, createStoryPayload)
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
        for (const img of response.data) {
          img.link = `http://localhost:7890/${img.image_path}`;
        }
        this.currentImages = response.data
      } catch (err: any) {
        this.error = err.message
      }
    },

    async deleteImage(imageId: number) {
      try {
        const response = await axios.delete(`${API_URL}/images/delete/${imageId}`)
        if (response.status === 200) {
          this.currentImages = this.currentImages.filter(img => img.id !== imageId)
        }
      } catch (err: any) {
        this.error = err.message
      }
    },

    // GET /chapter/all/{story_id}
    async fetchChapters(storyId: number) {
      try {
        const response = await axios.get(`${API_URL}/chapter/all/${storyId}`)
        this.currentChapters = response.data
        // By design, the only saved "messages" are the chapters generated by the assistant.
        // Viola has requested that the chapters are in their own section in the UI. Thus, when a new story is loaded, the messages[] will be empty
        // this.messages = this.currentChapters.map(chapter => ({ role: 'assistant', title: chapter.title, content: chapter.content }))
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
            // Remove the placeholder message. The content after the interrrupt will be handled in the resumeAfterInterrupt action
            this.messages.splice(messageIndex, 1)
            const [cleanContent, interruptMsg] = chunk.split('__interrupt__:');
            
            if (this.messages[messageIndex]) {
              this.messages[messageIndex].content += cleanContent;
            }
            this.interruptTriggered = true;

            if (interruptMsg !== undefined) {
              try {

                  this.interruptMessage = JSON.parse(interruptMsg.trim());
                  console.log("Parsed interrupt message:", this.interruptMessage);
                  if (this.interruptMessage !== undefined && this.interruptMessage !== null && this.interruptMessage.tool_name === "generate_image") {
                      this.imageGenInterruptTriggered = true;
                  }

              } catch (e) {
                  console.error("Failed to parse interrupt message", e);
                  this.interruptMessage = { tool_name: "unknown", message: `Could not parse interrupt message: ${e}`};
              }
            } else {
              this.interruptMessage = { tool_name: "unknown", message: "Received undefined interrupt message."}
            }
            
            this.streaming = false;
            return; 
          }

          if (this.messages[messageIndex]) {
            this.messages[messageIndex].content += chunk
          }
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
      this.imageGenInterruptTriggered = false
      this.error = null

      try {
        // Prepare Payload based on requirements
        const payload = {
          messages: this.messages, // Sending history context
          story_name: this.currentStory.title,
          thread_id: this.threadId,
          story_id: this.currentStory.id,
          story_length: this.currentStory.story_length,
          chapter_length: this.currentStory.chapter_length,
          genre: this.currentStory.genre,
          additional_notes: this.currentStory.additional_notes,
          main_characters: this.currentStory.main_characters,
          plot_ideas: this.currentStory.plot_ideas
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
    async resumeAfterInterrupt(userApproval: boolean, chapterId: number | null) {
      if (!this.currentStory) return

      // Reset interrupt state
      this.interruptTriggered = false
      this.imageGenInterruptTriggered = false
      this.interruptMessage = null
      this.streaming = true

      try {
        // Prepare Payload
        const payload = {
            story_name: this.currentStory.title,
            thread_id: this.threadId,
            story_id: this.currentStory.id,
            approval: userApproval,
            chapter_id: chapterId || -1, // Send -1 if no chapterId
            story_length: this.currentStory.story_length,
            chapter_length: this.currentStory.chapter_length,
            genre: this.currentStory.genre,
            additional_notes: this.currentStory.additional_notes,
            main_characters: this.currentStory.main_characters,
            plot_ideas: this.currentStory.plot_ideas
        }
        console.log("Resume Payload:", payload)

        const response = await fetch(`${API_URL}/messages/resume_after_interrupt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })

        if (!response.ok) throw new Error(response.statusText)
        
        await this._processStreamResponse(response)

      } catch (err: any) {
        this.error = err.message
        this.streaming = false
      } finally {
        // this.fetchStory(this.currentStory.id) // Refresh story data
        this.fetchImages(this.currentStory.id),
        this.fetchChapters(this.currentStory.id)
      }
    }
  }
})