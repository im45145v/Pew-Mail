from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.email.router import router as email_router
from app.api.ai.router import router as ai_router
from app.api.email.google_router import router as google_router

app = FastAPI(
    title="Pew Mail API",
    description="API for Pew Mail - AI-powered HTML Email Design, Management and Delivery Studio",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(email_router)
app.include_router(ai_router)
app.include_router(google_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Pew Mail API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)