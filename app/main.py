from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
import logging
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
from app.api.billing import router as billing_router
from app.api.customer_auth import router as customer_auth_router
from app.api.team import router as team_router
from app.api.knowledge_sources import router as knowledge_sources_router
from app.core.config import settings
from app.core.logging import configure_logging, correlation_id_var, tenant_id_var
from app.core.security import decode_access_token
from app.services.health_service import readiness_report
from app.services.metrics_service import metrics_report, record_request
from time import monotonic

configure_logging()
logger = logging.getLogger("followly.request")


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = monotonic()
        correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
        token = correlation_id_var.set(correlation_id)
        tenant_token = tenant_id_var.set("-")
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            payload = decode_access_token(authorization[7:]) or {}
            if payload.get("business_id") is not None:
                tenant_token = tenant_id_var.set(str(payload["business_id"]))
        try:
            response = await call_next(request)
            record_request(request.url.path, response.status_code, started_at)
            response.headers["X-Correlation-ID"] = correlation_id
            logger.info("request_completed method=%s path=%s status=%s", request.method, request.url.path, response.status_code)
            return response
        except Exception:
            record_request(request.url.path, 500, started_at)
            raise
        finally:
            correlation_id_var.reset(token)
            tenant_id_var.reset(tenant_token)


class OriginProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            public_webhooks = {"/api/v1/whatsapp/webhook", "/api/v1/billing/webhook"}
            allowed = set(cors_origins)
            if request.url.path not in public_webhooks and origin not in allowed:
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Origin is not trusted"}, status_code=403)
        return await call_next(request)

app = FastAPI(title="Followly API", version="1.0.0")
app.add_middleware(CorrelationMiddleware)
app.add_middleware(OriginProtectionMiddleware)

cors_origins = [
    origin.strip()
    for origin in (settings.CORS_ORIGINS or settings.FRONTEND_URL).split(",")
    if origin.strip()
]
if "*" in cors_origins:
    raise RuntimeError("CORS_ORIGINS cannot contain '*' when credentials are enabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
app.include_router(billing_router)
app.include_router(customer_auth_router)
app.include_router(team_router)
app.include_router(knowledge_sources_router)

@app.get("/")
def read_root():
    return {"message": "Followly API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/ready")
def readiness_check():
    return readiness_report()


@app.get("/health/metrics")
def metrics_check():
    return metrics_report()
