from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes.StoryRoute import story_router
from routes.MessagesRoute import messages_router
from routes.ImagesRouter import images_router
from routes.ChapterRouter import chapter_router
from services.postgres_service import PostgresService

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_instance = PostgresService()
    app.state.db = database_instance
    yield
    await database_instance.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def root():
    return {"message": "Tale Machine Backend is running."}

# Include routers
app.include_router(story_router)
app.include_router(messages_router)
app.include_router(images_router)
app.include_router(chapter_router)

if __name__ == "__main__":
    uvicorn.run(app, port=7890)