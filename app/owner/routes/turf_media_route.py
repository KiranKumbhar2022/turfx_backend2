import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.owner.schemas import turf_schema as schemas
from app.owner.models import turf_model as models
from app.database.database import getDB as get_db

routes = APIRouter(prefix="/turfs/{turf_id}/media", tags=["Photos & Videos"])

UPLOAD_DIR = Path("uploads")
MAX_PHOTO_MB = 10
MAX_VIDEO_MB = 100


def _save(file: UploadFile, kind: str, limit_mb: int) -> str:
    ext = Path(file.filename or "").suffix.lower()
    name = f"{uuid.uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(exist_ok=True)
    path = UPLOAD_DIR / name
    size = 0
    with open(path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > limit_mb * 1024 * 1024:
                out.close()
                path.unlink(missing_ok=True)
                raise HTTPException(413, f"{kind} exceeds {limit_mb} MB limit")
            out.write(chunk)
    return f"/uploads/{name}"


def _upload(turf_id: int, files: list[UploadFile], kind: str, limit: int, db: Session):
    if not db.get(models.Turf, turf_id):
        raise HTTPException(404, "Turf not found")
    prefix = "image/" if kind == "photo" else "video/"
    for f in files:
        if not (f.content_type or "").startswith(prefix):
            raise HTTPException(415, f"{f.filename}: expected a {kind} file")
    saved = []
    for f in files:
        row = models.Media(turf_id=turf_id, kind=kind, url=_save(f, kind, limit))
        db.add(row)
        saved.append(row)
    db.commit()
    for r in saved:
        db.refresh(r)
    return saved


@routes.post("/photos", response_model=list[schemas.MediaOut], status_code=201)
def upload_photos(
    turf_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    return _upload(turf_id, files, "photo", MAX_PHOTO_MB, db)


@routes.post("/video", response_model=list[schemas.MediaOut], status_code=201)
def upload_video(
    turf_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    return _upload(turf_id, files, "video", MAX_VIDEO_MB, db)


@routes.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(turf_id: int, media_id: int, db: Session = Depends(get_db)):
    m = db.get(models.Media, media_id)
    if not m or m.turf_id != turf_id:
        raise HTTPException(404, "Media not found")
    (UPLOAD_DIR / Path(m.url).name).unlink(missing_ok=True)
    db.delete(m)
    db.commit()
