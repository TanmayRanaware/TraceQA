from fastapi import APIRouter, UploadFile, File
from ..services.storage import save_object

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
	content = await file.read()
	uri = save_object(content, file.filename)
	return {"filename": file.filename, "uri": uri}
