from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
import secrets
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Business, Customer, Lead, Conversation
from app.core.security import decode_access_token
from app.services import conversation_service
from app.services.conversation_engine import process_message_with_agent
from app.services.business_config_service import get_business_configuration

router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory="app/templates")
QUICK_QUESTIONS = ["What services do you offer?", "How much does teeth whitening cost?", "I want to book a dental cleaning.", "What are your clinic hours?"]


@router.get("/widget.js", response_class=Response)
def widget_runtime():
    return Response(
        content="""(() => {
  const script = document.currentScript;
  const key = script && script.dataset.businessKey;
  if (!key) return;
  const origin = new URL(script.src).origin;
  const frame = document.createElement('iframe');
  frame.title = 'Followly chat';
  frame.src = origin + '/chat?business_key=' + encodeURIComponent(key);
  Object.assign(frame.style, {position:'fixed', right:'20px', bottom:'20px', width:'380px', height:'640px', border:'0', borderRadius:'18px', boxShadow:'0 12px 40px rgba(0,0,0,.25)', zIndex:'2147483647', background:'#fff'});
  document.body.appendChild(frame);
})();""",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, db: Session = Depends(get_db)):
    phone = request.cookies.get("followly_visitor_id") or f"web-{secrets.token_urlsafe(16)}"
    business_key = request.query_params.get("business_key", "")
    public_business = db.query(Business).filter(Business.widget_key == business_key).first() if business_key else None
    public_configuration = get_business_configuration(public_business) if public_business else None
    new_chat = request.query_params.get("new") == "1"
    selected_id = request.query_params.get("conversation_id")
    token = request.cookies.get("followly_customer_token")
    authenticated = False
    history = []
    chat_list = []
    if token:
        payload = decode_access_token(token) or {}
        customer_id = payload.get("customer_id")
        token_business_id = payload.get("business_id")
        customer = None
        if str(customer_id).isdigit() and str(token_business_id).isdigit():
            customer = db.query(Customer).filter(
                Customer.id == int(customer_id),
                Customer.business_id == int(token_business_id),
            ).first()
        if customer and payload.get("session_version", 0) != customer.session_version:
            customer = None
        authenticated = bool(customer and str(customer.business_id) == str(payload.get("business_id")) and customer.business.widget_key == business_key)
        if authenticated:
            lead = db.query(Lead).filter(Lead.customer_id == customer.id, Lead.business_id == customer.business_id).first()
            if lead:
                if customer.name and not lead.name:
                    lead.name = customer.name
                if customer.email and not lead.email:
                    lead.email = customer.email
                if lead.source == "whatsapp":
                    lead.source = "web"
                db.commit()
                if not new_chat:
                    conversation = db.query(Conversation).filter(
                        Conversation.lead_id == lead.id,
                        Conversation.business_id == customer.business_id,
                        Conversation.channel == "web",
                    )
                    if selected_id and selected_id.isdigit():
                        conversation = conversation.filter(Conversation.id == int(selected_id))
                    conversation = conversation.order_by(Conversation.last_message_at.desc()).first()
                    if conversation:
                        history = conversation_service.get_conversation_history(conversation.id, customer.business_id, limit=50, db=db)
                chat_list = [{"id": c.id, "title": c.lead.name or "Conversation", "updated": c.last_message_at.strftime("%b %d, %Y") if c.last_message_at else ""} for c in db.query(Conversation).filter(
                    Conversation.lead_id == lead.id,
                    Conversation.business_id == customer.business_id,
                    Conversation.channel == "web",
                ).order_by(Conversation.last_message_at.desc()).limit(20).all()]
    response = templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"messages": [{"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in history], "chat_list": chat_list, "new_chat": new_chat, "phone": phone, "business_key": business_key, "business_name": public_business.name if public_business else "", "branding": public_configuration.branding.model_dump() if public_configuration else {}, "channels": public_configuration.channels.enabled if public_configuration else {}, "authenticated": authenticated, "quick_questions": QUICK_QUESTIONS},
    )
    response.set_cookie(
        "followly_visitor_id",
        phone,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return response


@router.post("/chat", response_class=HTMLResponse)
async def chat_message(
    request: Request,
    message: str = Form(...),
    phone: str = Form(...),
    business_key: str = Form(...),
    new_chat: str = Form("0"),
    db: Session = Depends(get_db),
):
    token = request.cookies.get("followly_customer_token")
    payload = decode_access_token(token) if token else None
    customer_id = payload.get("customer_id") if payload else None
    token_business_id = payload.get("business_id") if payload else None
    customer = None
    if str(customer_id).isdigit() and str(token_business_id).isdigit():
        customer = db.query(Customer).filter(
            Customer.id == int(customer_id),
            Customer.business_id == int(token_business_id),
        ).first()
    if customer and payload.get("session_version", 0) != customer.session_version:
        customer = None
    business_for_key = db.query(Business).filter(
        Business.widget_key == business_key
    ).first()
    if not customer or not business_for_key or customer.business_id != business_for_key.id or str(customer.business_id) != str(payload.get("business_id")):
        raise HTTPException(status_code=401, detail="Sign in with Google before chatting")
    messages = []
    business = business_for_key
    if not business:
        messages.append({"role": "error", "content": "Demo business not found. Run the seed script first."})
        return templates.TemplateResponse(
            request=request, name="chat.html",
            context={"messages": messages, "phone": phone, "business_key": business_key, "business_name": business.name, "quick_questions": QUICK_QUESTIONS},
            status_code=404,
        )

    lead = db.query(Lead).filter(Lead.customer_id == customer.id, Lead.business_id == business.id).first()
    if not lead:
        lead = conversation_service.get_or_create_lead(phone, business.id, db)
    changed = False
    if lead.customer_id != customer.id:
        lead.customer_id = customer.id
        changed = True
    if customer.name and lead.name != customer.name:
        lead.name = customer.name
        changed = True
    if customer.email and lead.email != customer.email:
        lead.email = customer.email
        changed = True
    if lead.source != "web":
        lead.source = "web"
        changed = True
    if changed:
        db.commit()
    if new_chat == "1":
        conversation = Conversation(lead_id=lead.id, business_id=business.id, channel="web")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    else:
        conversation = conversation_service.get_or_create_conversation(lead.id, business.id, "web", db)
    conversation_service.save_message(conversation.id, business.id, "user", message, db)
    response = await process_message_with_agent(conversation, business, message, db)
    conversation_service.save_message(conversation.id, business.id, "assistant", response, db)
    history = conversation_service.get_conversation_history(conversation.id, business.id, limit=50, db=db)
    messages = [{"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in history]
    return templates.TemplateResponse(
        request=request, name="chat.html",
        context={"messages": messages, "phone": phone, "business_key": business_key, "business_name": business.name, "quick_questions": QUICK_QUESTIONS},
    )
