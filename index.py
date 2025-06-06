from fastapi import FastAPI, HTTPException, UploadFile
app = FastAPI()

from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta
import json

from helpers.mongo_connect import mongo_create_one, mongo_find_one
from helpers.password_utils import verify_password

from helpers.agent import chat, pdf_upload
from pydantic import BaseModel
from helpers.middleware import JWTMiddleware
from helpers.jwt_utils import create_token
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

import tempfile
import os


class Message(BaseModel):
    message: list[dict[str, str]]

class LoginRequest(BaseModel):
    username: str
    password: str

app.add_middleware(JWTMiddleware)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

@app.get("/")
def serve_react_app():
    return FileResponse("frontend/index.html")

@app.get("/ping")
def read_root():
    return {"ping": "pong"}

@app.post("/login")
def login(data: LoginRequest, response: Response):
    if data.password == "" or data.username == "":
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = mongo_find_one({"username": data.username}, "users")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(data.password, user.get("password")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_token({"sub": user.get("_id")}, timedelta(days=1))

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=86400,
        path="/",
    )

    return {"message": "Logged in, token set in cookie", "success": True}

@app.get("/user")
def user(response: Response):
    return {"message": "User is logged in", "success": True}

@app.post("/chat")
def chat_handler(message: Message):
    resp = chat(message.message)
    msg = json.loads(resp[-1].get("content")).get("content")
    mongo_create_one({"message": resp[1:], "created_at": datetime.now()}, "chats")
    return {"message": "response recieved", "success": True, "data": msg}

@app.post("/doc")
async def doc_handler(file: UploadFile):
    if file.filename == "":
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    pdf_upload(tmp_path)
    os.remove(tmp_path)
    return {"message": "File uploaded successfully", "success": True}

@app.post("/search")
async def search_handler(message: Message):
    if message.message == "":
        raise HTTPException(status_code=400, detail="No message")
    