from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS para integración con frontend
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Basic file upload endpoint
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
	upload_dir = "documents"
	os.makedirs(upload_dir, exist_ok=True)
	file_location = os.path.join(upload_dir, file.filename)
	with open(file_location, "wb") as f:
		f.write(await file.read())
	return JSONResponse(content={"filename": file.filename, "message": "File uploaded successfully."})
