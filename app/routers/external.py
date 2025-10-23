#routers/external.py
from fastapi import APIRouter, HTTPException
import httpx, asyncio
from app.config import settings
import redis.asyncio as aioredis
import json

router = APIRouter(prefix="/external", tags=["external"])
redis = None

@router.on_event("startup")
async def startup_redis():
    global redis
    redis = await aioredis.from_url(settings.REDIS_URL)

@router.get("/weather")
async def get_weather(city: str):
    key = f"weather:{city.lower()}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    # пример внешнего вызова (псевдо)
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=YOUR_KEY")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="External API error")
        data = resp.json()
        await redis.set(key, json.dumps(data), ex=300)
        return data
