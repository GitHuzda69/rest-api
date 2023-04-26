from fastapi import APIRouter, File, UploadFile
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseUpload
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import io
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/api-collections", tags=["Google Drive"])

# Konfigurasi kredensial Oauth
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client.json'

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

@router.get("/cari_folder/{nama}/")
async def list_files(nama: str):
    """Menampilkan daftar file pada Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    # Panggil API untuk mengambil daftar file pada Google Drive
    query = "name contains '{}'".format(nama) if nama else ""
    results = drive_service.files().list(
        q=query,
        pageSize=10,
        fields="nextPageToken, files(id, name)"
    ).execute()
    
    items = results.get("files", [])
    if not items:
        return JSONResponse(content={"message": "Tidak ada file yang ditemukan."})
    else:
        file_list = []
        for item in items:
            file_list.append({"name": item["name"], "id": item["id"]})
        return JSONResponse(content={"files": file_list})

@router.post("/copy_file/{file_id}")
async def create_copy(file_id: str):
    """Membuat salinan file dengan ID tertentu di Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    try:
        # Panggil API untuk membuat salinan file
        copied_file = drive_service.files().copy(
            fileId=file_id,
            body={
                'name': 'Copy of ' + file_id  # nama file salinan
            }
        ).execute()
        
        # Tampilkan hasil
        return JSONResponse(content={
            "message": "Berhasil membuat salinan file.",
            "original_file_id": file_id,
            "copied_file_id": copied_file['id']
        })
    except HttpError as error:
        # Jika terjadi error saat membuat salinan file, tampilkan pesan error
        return JSONResponse(content={"message": str(error)})

@router.post("/pindah_file/{file_id}/{from_folder_id}/{to_folder_id}")
async def move_file(file_id: str, from_folder_id: str, to_folder_id: str):
    """Memindahkan file dari satu folder ke folder lain pada Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    # Panggil API untuk memindahkan file
    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    file = drive_service.files().update(fileId=file_id,
                                         addParents=to_folder_id,
                                         removeParents=from_folder_id,
                                         fields='id, parents').execute()
    
    # Cek apakah file berhasil dipindahkan
    if previous_parents == ",".join(file.get('parents')):
        return JSONResponse(content={"message": "File tidak berhasil dipindahkan."})
    else:
        return JSONResponse(content={"message": "File berhasil dipindahkan."})

@router.post("/ganti_file/{file_id}")
async def upload_file(file_id: str, file: UploadFile):
    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()
        
        # Panggil API untuk mendapatkan metadata file
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        
        # Buat metadata file baru dengan menggunakan nama file yang diupload
        new_file_metadata = {
            'name': file.filename,
            'mimeType': file.content_type
        }
        
        # Jika nama file baru sama dengan nama file lama, update file
        if new_file_metadata['name'] == file_metadata['name']:
            media = MediaIoBaseUpload(file.file, mimetype=file.content_type, chunksize=1024*1024, resumable=True)
            request = drive_service.files().update(fileId=file_id, media_body=media)
            request.execute()
        else:
            # Buat request untuk mengupdate metadata file
            request = drive_service.files().update(fileId=file_id, body=new_file_metadata).execute()
            
            # Buat request untuk mengupdate isi file
            media = MediaIoBaseUpload(file.file, mimetype=file.content_type, chunksize=1024*1024, resumable=True)
            request = drive_service.files().update(fileId=file_id, media_body=media)
            request.execute()
        
        return {"message": "File berhasil diunggah dan diganti"}
    
    except HttpError as error:
        print(f'An error occurred: {error}')
        return {"message": "Terjadi kesalahan saat mengunggah file"}

@router.get("/cari_file/{nama}/")
async def list_files(nama: str):
    """Menampilkan daftar file pada Google Drive berdasarkan nama file"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    # Panggil API untuk mengambil daftar file pada Google Drive
    query = "name contains '{}'".format(nama) if nama else ""
    results = drive_service.files().list(
        q=query,
        pageSize=10,
        fields="nextPageToken, files(id, name)"
    ).execute()
    
    items = results.get("files", [])
    if not items:
        return JSONResponse(content={"message": "Tidak ada file yang ditemukan."})
    else:
        file_list = []
        for item in items:
            file_list.append({"name": item["name"], "id": item["id"]})
        return JSONResponse(content={"files": file_list})

@router.post("/bagikan_file/{file_id}/{email_address}")
async def bagikan_file(email_address: str, file_id: str, role: str, type: str, with_link: bool):
    """Menambahkan cakupan berbagi ke preferensi berbagi file"""
    # Service Drive
    drive_service = create_drive_service()

    # Mengambil informasi file yang ingin dibagikan
    file = drive_service.files().get(fileId=file_id, fields='id, name, mimeType, permissions').execute()

    # Memeriksa apakah file sudah dibagikan dengan pengguna yang dimaksud
    email = email_address
    existing_permissions = [perm for perm in file.get('permissions', []) if perm.get('emailAddress') == email]
    if existing_permissions:
        print(f"File {file.get('name')} sudah dibagikan dengan {email}")
        return {"message": f"File {file.get('name')} sudah dibagikan dengan {email}"}

    # Menambahkan izin akses baru ke file
    permission = {
        'type': type,
        'role': role,
        'emailAddress': email,
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()

    # Membuat URL berbagi jika diinginkan
    if with_link:
        link_permission = {
            'type': 'anyone',
            'role': 'reader',
            'allowFileDiscovery': False,
        }
        link = drive_service.permissions().create(fileId=file_id, body=link_permission, fields='id, webLink').execute().get('webLink')
        print(f"Berhasil membagikan file {file.get('name')} dengan {email} dan URL berbagi: {link}")
        return {"message": f"Berhasil membagikan file {file.get('name')} dengan {email} dan URL berbagi: {link}"}

    # Jika URL berbagi tidak diminta, kembalikan pesan sukses
    print(f"Berhasil membagikan file {file.get('name')} dengan {email}")
    return {"message": f"Berhasil membagikan file {file.get('name')} dengan {email}"}

@router.get("/list_folders")
async def list_folders():
    """Menampilkan daftar folder pada Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()
    
    # Panggil API untuk mengambil daftar folder pada Google Drive
    query = "mimeType='application/vnd.google-apps.folder'"
    results = drive_service.files().list(
        q=query,
        pageSize=10,
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

@router.get("/list_file_serta_directori_parent_mereka", tags="")
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

# membuat folder di google drive
@router.post("/create_folder/")
async def create_folder(name: str):
    """Membuat folder baru di Google Drive"""
    # Buat service Drive menggunakan credentials yang sudah di-load
    drive_service = create_drive_service()

    # Definisikan metadata folder
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    # Buat folder baru di Google Drive
    folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    return JSONResponse(content={"message": f"Folder '{name}' telah dibuat dengan ID: {folder.get('id')}"})

# mencari atau membuat folder dengan nama tertentu v2
@router.post("/find_or_create_folder/")
async def find_or_create_folder(name: str):
    """Mencari atau membuat folder di Google Drive dengan nama tertentu"""

    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()

        # Definisikan parameter untuk mencari folder dengan nama tertentu
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        fields = "nextPageToken, files(id, name)"

        # Cari folder dengan nama tertentu di Google Drive
        results = drive_service.files().list(q=query, fields=fields).execute()
        items = results.get("files", [])

        # Jika folder dengan nama tertentu sudah ada, kembalikan ID folder tersebut
        if items:
            folder = items[0]
            return JSONResponse(content={"message": f"Folder '{name}' telah ditemukan dengan ID: {folder.get('id')}"})

        # Jika folder dengan nama tertentu belum ada, buat folder baru
        folder_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = drive_service.files().create(body=folder_metadata, fields="id").execute()

        return JSONResponse(content={"message": f"Folder '{name}' telah dibuat dengan ID: {folder.get('id')}"})

    except HttpError as error:
        return JSONResponse(content={"message": f"An error occurred: {str(error)}"}, status_code=500)
    
# menyalin file dari layanan lain ke google drive    
@router.post("/copy_file_to_drive/")
async def copy_file_to_drive(name: str, url: str):
    """Menyalin file dari layanan lain ke Google Drive"""

    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()

        # Unduh file dari layanan lain
        response = requests.get(url)
        file_content = BytesIO(response.content)

        # Buat metadata file yang akan diunggah
        file_metadata = {'name': name}

        # Unggah file ke Google Drive
        file = drive_service.files().create(
            body=file_metadata,
            media_body=MediaIoBaseUpload(file_content, mimetype=response.headers.get('Content-Type')),
            fields='id'
        ).execute()

        return JSONResponse(content={"message": f"File '{name}' telah disalin ke Google Drive dengan ID: {file.get('id')}"})

    except HttpError as error:
        return JSONResponse(content={"message": f"An error occurred: {str(error)}"}, status_code=500)#
    
# mencari atau membuat file dengan nama tertentu v2    
@router.post("/find_or_create_file/")
async def find_or_create_file(name: str):
    """Mencari atau membuat file di Google Drive dengan nama tertentu"""

    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()

        # Definisikan parameter untuk mencari file dengan nama tertentu
        query = f"name='{name}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
        fields = "nextPageToken, files(id, name, mimeType)"

        # Cari file dengan nama tertentu di Google Drive
        results = drive_service.files().list(q=query, fields=fields).execute()
        items = results.get("files", [])

        # Jika file dengan nama tertentu sudah ada, kembalikan ID file tersebut
        if items:
            file = items[0]
            return JSONResponse(content={"message": f"File '{name}' telah ditemukan dengan ID: {file.get('id')}"})

        # Jika file dengan nama tertentu belum ada, buat file baru
        file_metadata = {
            "name": name
        }
        file = drive_service.files().create(body=file_metadata, fields="id").execute()

        return JSONResponse(content={"message": f"File '{name}' telah dibuat dengan ID: {file.get('id')}"})

    except HttpError as error:
        return JSONResponse(content={"message": f"An error occurred: {str(error)}"}, status_code=500)

# membuat pintasan file di google drive  
@router.post("/create_shortcut/")
async def create_shortcut(name: str, target_file_id: str):
    """Membuat pintasan (shortcut) ke file tertentu di Google Drive"""

    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()

        # Buat metadata untuk pintasan file
        shortcut_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.shortcut",
            "shortcutDetails": {
                "targetId": target_file_id
            }
        }

        # Buat pintasan file di Google Drive
        shortcut = drive_service.files().create(body=shortcut_metadata, fields="id").execute()

        return JSONResponse(content={"message": f"Pintasan '{name}' telah dibuat dengan ID: {shortcut.get('id')}"})

    except HttpError as error:
        return JSONResponse(content={"message": f"An error occurred: {str(error)}"}, status_code=500)

@router.post("/create_file/{nama}")
async def create_file(nama: str):
    name = nama
    try:
        # Buat service Drive menggunakan credentials yang sudah di-load
        drive_service = create_drive_service()

        file_metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.document'}
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        
        return f'File ID: {file.get("id")}'
    except:
        return JSONResponse(content={"message": "file gagal dibuat"})