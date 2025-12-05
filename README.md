# TaleMachine

TaleMachine is an AI-powered storytelling platform that enables users to create, share, and explore interactive stories. Whether you're a writer looking to craft engaging narratives or a reader seeking immersive experiences, TaleMachine offers tools and features to bring your stories to life.

## Features

### Story-Driven Workflow

The application is organized around **stories**. Whenever you start a new chat session with the AI, you simply specify which story and some details about it to set the context. Just fill a few fields like title, genre, main characters, and plot ideas to get started.

### Chapters and Saving

Stories are built from individual chapters. You can ask the AI to write a new chapter or use the chat to edit and refine the text.

It is important to note that _chat message history is not stored_. To keep your progress, you must explicitly instruct the AI to **save the chapter**. Once saved, the chapter is stored permanently, allowing you to pause and resume writing your story at any time. You can always view and manage your saved chapters in the frontend interface.

It is also possible to save chapters out of order by specifying the `previous_chapter_id` when saving. This allows you to insert chapters at specific points in your story.

### Worldbuilding with Neo4j

To support rich storytelling and consistent character development, the application uses Neo4j. This database tracks entities and their relationships (like characters and locations). You can also view a visual graph of these connections to better understand the structure of your story.
To view the graph, navigate to your story and select the 'Graph' tab in the frontend.

### Image Generation

You can generate images using prompts directly within the app. After an image is generated, you have the option to link it to a specific chapter, though this is not required. All images are collected and viewable in the frontend gallery.

## Technologies Used

- **FastAPI**: Backend framework for building the API.
- **PostgreSQL**: Primary database for storing stories, chapters, and user data.
- **Neo4j**: Graph database for managing entities and relationships within stories.
- **LangChain**: Framework for building AI applications with language models.
- **Docker**: Containerization platform for easy deployment and management of services.

### AI Models

The application uses Gemini models from Gemini API and Vertex AI for natural language processing and image generation tasks.

- `gemini-2.5-flash-image` for image generation.
- `gemini-2.5-flash-lite` for text generation.
