import os
import uuid
from pathlib import Path
from pwdlib import PasswordHash
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import setting
from fastapi import HTTPException, UploadFile


passwordHash=PasswordHash.recommended()


# Document storage directory
UPLOAD_DIR = Path("uploads/owners")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf"
}


def save_document(
    file: UploadFile,
    document_type: str
) -> str:

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {document_type} file format"
        )

    if file.content_type not in {
        "image/jpeg",
        "image/png",
        "application/pdf"
    }:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {document_type} content type"
        )

    content = file.file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail=f"{document_type} file is empty"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"{document_type} must be under 5 MB"
        )

    folder = UPLOAD_DIR / document_type
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = folder / filename

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return str(file_path).replace("\\", "/")


def delete_uploaded_files(paths: list[str]):

    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

def hashPassword(password:str):
    return passwordHash.hash(password)

def verifyPassword(password:str, hashPassword):
    return passwordHash.verify(password,hashPassword)  

def createAccessToken(data: dict):
    toEncoded = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    toEncoded.update({"exp": expire})

    encodedJwtToken = jwt.encode(
        toEncoded,
        setting.SECRET_KEY,
        algorithm=setting.ALGORITHM
    )

    return encodedJwtToken    
