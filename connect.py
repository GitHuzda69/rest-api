from fastapi import FastAPI, Request, Depends, File, Header, HTTPException, Body, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import RedirectResponse
from starlette.requests import Request

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

from pydantic import BaseModel
from datetime import datetime

import requests
from io import BytesIO
import os
import io
import json
import pytz
import logging
import httpx
import time

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger((__name__))
WEBHOOK_URL = "http://localhost:8000/log"

SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_848310059846-m3j1ltsqheqg5sjpaigv6e2bst17s312.apps.googleusercontent.com.json'

class CreateFileModel(BaseModel):
    name: str

class CreateFileFolder(BaseModel):
    folder_id : str

class WebhookCreateFile(BaseModel):
    name: str
    date: str

def create_drive_service():
    """Membuat Drive service menggunakan kredensial Oauth"""
    credentials = None
    # Coba untuk memuat credentials dari file token.json
    try:
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    except Exception as e:
        print('Tidak dapat memuat kredensial Oauth: ' + str(e))
    # Jika credentials belum ada, maka buat credentials dengan melakukan Oauth flow
    # if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            credentials = flow.run_local_server(port=63176)
        # Simpan credentials yang berhasil dibuat ke file token.json
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

@app.post("/create_file_in_folder/{name}/{folder_id}")
async def create_file_in_folder(name: str, folder_id: str):
    try:
        # Build the Drive API client
        drive_service = create_drive_service()

        # Set the metadata for the new file
        file_metadata = {'name': name, 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.document'}

        # Create the file in the specified folder
        file = drive_service.files().create(body=file_metadata).execute()
        file_id = file.get('id')

        webhook_create_file = WebhookCreateFile(name=name, date=datetime.now().isoformat())
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(WEBHOOK_URL, json=webhook_create_file.dict())
                response.raise_for_status()
                logger.info("Webhook sent successfully")
        except (httpx.HTTPError, httpx.RequestError) as e:
            logger.error(f"Failed to send webhook: {e}")

        return f'Create file successfully. File ID: {file_id}'
    except Exception as e:
        return JSONResponse(content={"message": "Create file failed, error: " + str(e)})

    
@app.post("/log")
async def webhook_handler(payload: WebhookCreateFile):
    # Mendapatkan informasi dari payload
    name = payload.name
    date = payload.date


    # Melakukan operasi atau pemrosesan sesuai kebutuhan
    # Contoh: Menampilkan log pesan dengan informasi file dan folder yang baru dibuat
    logger.info(f"New file created: {name}. Created at: {date}")

    # Mengembalikan respons sukses
    return {"status": "success"}
