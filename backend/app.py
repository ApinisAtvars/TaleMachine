from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from backend.routes.StoryRoute import story_router
from backend.routes.MessagesRoute import messages_router
from backend.services.postgres_service import PostgresService

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_instance = PostgresService()
    await database_instance.connect()
    app.state.db = database_instance
    yield
    await database_instance.disconnect()

@app.get("/health")
async def root():
    return {"message": "Tale Machine Backend is running."}

# Include routers
app.include_router(story_router)
app.include_router(messages_router)

if __name__ == "__main__":
    uvicorn.run(app, port=7890)