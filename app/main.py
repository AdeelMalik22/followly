from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.whatsapp import router as whatsapp_router
from app.api.calendar import router as calendar_router
from app.api.chat import router as chat_router
from app.api.pages import router as pages_router

app = FastAPI(title="Followly API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(whatsapp_router)
app.include_router(calendar_router)
app.include_router(chat_router)
app.include_router(pages_router)

@app.get("/")
def read_root():
    return {"message": "Followly API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
