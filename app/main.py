import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.transcribe import TranscribeService
from app.services.order_processor import process_order
from app.api import products, health

app = FastAPI(title="Grocery Voice-to-Response API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router, prefix="/products")

_transcribe = TranscribeService()


@app.websocket("/ws/order")
async def order_websocket(
    websocket: WebSocket, db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    transcript_queue: asyncio.Queue = asyncio.Queue()

    async def process_transcripts():
        while True:
            transcript = await transcript_queue.get()
            if transcript is None:
                break
            try:
                order = await process_order(transcript, db)
                await websocket.send_json(order.model_dump(mode="json"))
            except Exception as exc:
                await websocket.send_json({"error": str(exc)})

    processor = asyncio.create_task(process_transcripts())

    try:
        await _transcribe.stream(websocket, transcript_queue)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await transcript_queue.put(None)
        await processor
