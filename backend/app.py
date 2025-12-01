from fastapi import FastAPI
import uvicorn
from services.agent import TaleMachineAgent

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Tale Machine Backend is running."}

if __name__ == "__main__":
    uvicorn.run(app, port=7890)