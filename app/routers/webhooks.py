#routers/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import hmac, hashlib
from app.config import settings
from app.database import AsyncSessionLocal
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
SECRET = "webhook-secret"

@router.post("/provider")
async def webhook_provider(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Signature", "")
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")
    payload = json.loads(body)
    event_id = payload.get("id")
    # реализовать идемпотентность: проверить в БД, обработан ли event_id
    # сохранить событие
    return {"status": "ok"}
