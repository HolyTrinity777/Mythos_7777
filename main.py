from fastapi import FastAPI
from routers.api_router import api_router

app = FastAPI(
    title="ASI Competition API",
    description="Autonomous Superintelligence API for competition dominance with full proof and governance",
    version="1.0.0"
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "ASI Competition API Ready"}
