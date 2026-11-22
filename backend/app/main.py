
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Enterprise AI Customer Support Assistant",
    description="RAG-powered E-Commerce Customer Support API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api")


@app.get("/")
def home():
    return {
        "message": "AI Customer Support Assistant API is running!"
    }



@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
