from fastapi import Header, HTTPException, Depends
from fastapi.responses import JSONResponse
import os

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")