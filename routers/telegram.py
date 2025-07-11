from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from services.supabase import update_user_telegram_id

router = APIRouter()

class TelegramLinkRequest(BaseModel):
    user_token: str
    chat_id: int

@router.post("/api/link-telegram")
async def link_telegram(req: TelegramLinkRequest):
    try:
        user_id = req.user_token
        response = update_user_telegram_id(user_id, req.chat_id)
        if response.data:
            logging.info(f"Linked chat_id {req.chat_id} to user_id {user_id}")
            return {"status": "success"}
        else:
            logging.error(f"No profile found for user_id {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logging.error(f"Failed to link Telegram: {e}")
        raise HTTPException(status_code=500, detail="Failed to link Telegram") 