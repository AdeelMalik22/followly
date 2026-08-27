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


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"messages": [], "business_id": "", "phone": "demo-user"},
    )


@router.post("/chat", response_class=HTMLResponse)
async def chat_message(
    request: Request,
    message: str = Form(...),
    business_id: int = Form(...),
    phone: str = Form("demo-user"),
    db: Session = Depends(get_db),
):
    messages = [{"role": "user", "content": message}]
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        messages.append({"role": "error", "content": "Business not found."})
        return templates.TemplateResponse(
            request=request, name="chat.html",
            context={"messages": messages, "business_id": business_id, "phone": phone},
            status_code=404,
        )

    lead = conversation_service.get_or_create_lead(phone, business.id, db)
    conversation = conversation_service.get_or_create_conversation(
        lead.id, business.id, "web", db
    )
    conversation_service.save_message(conversation.id, "user", message, db)
    response = await process_message_with_agent(conversation, business, message, db)
    conversation_service.save_message(conversation.id, "assistant", response, db)
    messages.append({"role": "assistant", "content": response})
    return templates.TemplateResponse(
        request=request, name="chat.html",
        context={"messages": messages, "business_id": business_id, "phone": phone},
    )
