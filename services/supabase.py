import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_users_with_filters_and_telegram():
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    profiles = supabase.table("profiles") \
        .select("*") \
        .neq("telegram_id", None) \
        .or_(f"is_paid.eq.true,trial_end.gte.{now}") \
        .execute().data
    result = []
    for user in profiles:
        filters = supabase.table("filters").select("*").eq("user_id", user["id"]).execute().data
        user_filters = []
        for f in filters:
            keywords = [k["keyword"] for k in supabase.table("filter_keywords").select("*").eq("filter_id", f["id"]).execute().data]
            categories = [c["category"] for c in supabase.table("filter_categories").select("*").eq("filter_id", f["id"]).execute().data]
            user_filters.append({
                "id": f["id"],
                "name": f["name"],
                "min_price": float(f["min_price"]) if f["min_price"] is not None else None,
                "max_price": float(f["max_price"]) if f["max_price"] is not None else None,
                "keywords": keywords,
                "categories": categories
            })
        result.append({
            "user_id": user["id"],
            "telegram_id": user["telegram_id"],
            "filters": user_filters
        })
    return result

def update_user_telegram_id(user_id: str, chat_id: int):
    response = supabase.table("profiles").update({"telegram_id": str(chat_id)}).eq("id", user_id).execute()
    return response 