import os
import shutil
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ....core.config import settings
from ....models.types import FileEntry

router = APIRouter(tags=["global-files"])

# Use settings.GLOBAL_FILES_DIR
GLOBAL_FILES_DIR = settings.GLOBAL_FILES_DIR

@router.post("")
async def upload_global_file(file: UploadFile = File(...)):
    """Upload a global file accessible to all agents."""
    file_path = GLOBAL_FILES_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    file_entry = FileEntry(
        id=str(uuid.uuid4()),
        name=file.filename,
        type=file.filename.split('.')[-1] if '.' in file.filename else "bin",
        content="",
        size=os.path.getsize(file_path),
        uploaded_at=datetime.utcnow().isoformat()
    )
    return file_entry

@router.get("", response_model=List[FileEntry])
async def list_global_files():
    """List all global files."""
    files = []
    for filename in os.listdir(GLOBAL_FILES_DIR):
        file_path = GLOBAL_FILES_DIR / filename
        if file_path.is_file():
            files.append(FileEntry(
                id=filename,
                name=filename,
                type=filename.split('.')[-1] if '.' in filename else "bin",
                content="",
                size=os.path.getsize(file_path),
                uploaded_at=datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            ))
    return files

@router.get("/{filename}")
async def download_global_file(filename: str):
    """Download a global file."""
    file_path = GLOBAL_FILES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

@router.delete("/{filename}")
async def delete_global_file(filename: str):
    """Delete a global file."""
    file_path = GLOBAL_FILES_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")
