from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, upload, versions, tests, requirements, background_tasks, config, vector_db

app = FastAPI(
    title="Enterprise Requirements AI",
    description="AI-powered system for managing enterprise banking requirements and generating test cases",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(versions.router)
app.include_router(tests.router)
app.include_router(requirements.router)
app.include_router(background_tasks.router)
app.include_router(config.router)
app.include_router(vector_db.router)

@app.get("/")
async def root():
    return {
        "message": "Enterprise Requirements AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
