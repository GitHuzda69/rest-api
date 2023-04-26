from fastapi import FastAPI
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from fastapi.requests import Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Konfigurasi kredensial Oauth
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_848310059846-m3j1ltsqheqg5sjpaigv6e2bst17s312.apps.googleusercontent.com.json'

# membuat konektivitas dengan drive
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

@app.get("/list_folders")
async def list_folders():
    """Menampilkan daftar folder pada Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    # Panggil API untuk mengambil daftar folder pada Google Drive
    query = "mimeType='application/vnd.google-apps.folder'"
    results = drive_service.files().list(
        q=query,
        fields="nextPageToken, files(id, name)"
    ).execute()
    
    items = results.get("files", [])
    if not items:
        return JSONResponse(content={"message": "Tidak ada folder yang ditemukan."})
    else:
        folder_list = []
        for item in items:
            folder_list.append({"name": item["name"], "id": item["id"]})
        return JSONResponse(content={"folders": folder_list})

# Fungsi Memberikan List File dengan Parent
@app.get("/list_file_serta_directori_parent_mereka", tags="")
async def list_files():
    """Mengeksekusi permintaan daftar file dan folder di Google Drive"""
    # Service Drive
    drive_service = create_drive_service()

    # Mengambil semua file dan folder di Google Drive
    files = []
    nextPageToken = None

    while True:
        query = "trashed = false"
        if nextPageToken:
            query += f" and '{nextPageToken}' in parents"
        response = drive_service.files().list(q=query, fields="nextPageToken, files(id, name, parents)").execute()
        items = response.get('files', [])
        files.extend(items)
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break

    while nextPageToken:
        nextPage = drive_service.files().list(q="trashed = false", fields="nextPageToken, files(id, name, parents)", pageToken=nextPageToken).execute().get('files', [])
        files += nextPage
        nextPageToken = nextPageToken.get('nextPageToken')

    # Membuat dictionary untuk menyimpan file dan folder beserta lokasinya
    result = {}

    for file in files:
        parents = file.get('parents', [])
        path = []
        for parent in parents:
            parent_name = drive_service.files().get(fileId=parent, fields='name').execute().get('name')
            path.append(parent_name)
        path.reverse()
        path.append(file.get('name'))
        result[file.get('id')] = '/'.join(path)

    return JSONResponse(result)

@app.post("/watch_folder/")
async def watch_folder(folder_id: str):
    drive_service = create_drive_service()

    body = {
        'id': folder_id,
        'type': "web_hook",
        'address': "https://eo5iykl420ws52e.m.pipedream.net"
    }
    try:
        watch = drive_service.files().watch(
            fileId= folder_id,
            body=body
        ).execute()

        return JSONResponse(content={"message": f"folder id : '{folder_id}' berhasil."})
    except HttpError as error:
        return JSONResponse(content={'Error': str(error)})

@app.post("/watch_file/")
async def watch_file(file_id: str):
    drive_service = create_drive_service()

    body = {
        'id': file_id,
        'type': "web_hook",
        'address': "https://eo5iykl420ws52e.m.pipedream.net"
    }
    try:
        watch = drive_service.files().watch(
            fileId=file_id,
            body=body
        ).execute()

        return JSONResponse(content={"message": f"file id : '{file_id}' berhasil."})
    except HttpError as error:
        return JSONResponse(content={"message": f"file id : '{file_id}' gagal. Error: {error}"})




