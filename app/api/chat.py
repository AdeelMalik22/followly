from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Business
from app.services import conversation_service
from app.services.conversation_engine import process_message_with_agent

router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory="app/templates")
QUICK_QUESTIONS = ["What services do you offer?", "How much does teeth whitening cost?", "I want to book a dental cleaning.", "What are your clinic hours?"]


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"messages": [], "phone": "demo-user", "business_key": request.query_params.get("business_key", ""), "quick_questions": QUICK_QUESTIONS},
    )


@router.post("/chat", response_class=HTMLResponse)
async def chat_message(
    request: Request,
    message: str = Form(...),
    phone: str = Form("demo-user"),
    business_key: str = Form(...),
    db: Session = Depends(get_db),
):
    messages = []
    # Compare JSON settings in Python for SQLite/PostgreSQL compatibility.
    business = next(
        (item for item in db.query(Business).all()
         if (item.settings or {}).get("widget_key") == business_key),
        None,
    )
    if not business:
        messages.append({"role": "error", "content": "Demo business not found. Run the seed script first."})
        return templates.TemplateResponse(
            request=request, name="chat.html",
            context={"messages": messages, "phone": phone, "business_key": business_key, "quick_questions": QUICK_QUESTIONS},
            status_code=404,
        )

    lead = conversation_service.get_or_create_lead(phone, business.id, db)
    conversation = conversation_service.get_or_create_conversation(
        lead.id, business.id, "web", db
    )
    conversation_service.save_message(conversation.id, "user", message, db)
    response = await process_message_with_agent(conversation, business, message, db)
    conversation_service.save_message(conversation.id, "assistant", response, db)
    history = conversation_service.get_conversation_history(conversation.id, limit=50, db=db)
    messages = [{"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in history]
    return templates.TemplateResponse(
        request=request, name="chat.html",
        context={"messages": messages, "phone": phone, "business_key": business_key, "quick_questions": QUICK_QUESTIONS},
    )
