from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.whatsapp import router as whatsapp_router
from app.api.calendar import router as calendar_router
from app.api.chat import router as chat_router
from app.api.pages import router as pages_router
from app.api.conversations import router as conversations_router
from app.api.leads import router as leads_router
from app.api.appointments import router as appointments_router
from app.api.analytics import router as analytics_router
from app.api.follow_up_rules import router as follow_up_rules_router
from app.api.business import router as business_router

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
app.include_router(conversations_router)
app.include_router(leads_router)
app.include_router(appointments_router)
app.include_router(analytics_router)
app.include_router(follow_up_rules_router)
app.include_router(business_router)

@app.get("/")
def read_root():
    return {"message": "Followly API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
