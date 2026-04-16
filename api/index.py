from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import os

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel Environment Variable (Secure way to store API keys)
MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_XGFW9ksTpnyV6vfvheprTk9KvBUT1Em8rTg8")
HEADERS = {"Authorization": f"Bearer {MESHY_API_KEY}"}

@app.post("/api/generate-3d")
async def generate_3d(file: UploadFile = File(...)):
    """Step 1: Upload image and start the 3D generation task."""
    contents = await file.read()
    
    if MESHY_API_KEY == "YOUR_MESHY_API_KEY_HERE":
        return {"error": "API Key is missing. Please add MESHY_API_KEY in your Vercel Environment Variables."}
    
    encoded_string = base64.b64encode(contents).decode('utf-8')
    payload = {
        "image_url": f"data:{file.content_type};base64,{encoded_string}",
        "enable_pbr": True
    }
    
    # Start task on Meshy
    response = requests.post("https://api.meshy.ai/v1/image-to-3d", headers=HEADERS, json=payload)
    response_data = response.json()
    task_id = response_data.get("result")
    
    if not task_id:
        return {"error": "Failed to start task", "details": response_data}
    
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
def check_status(task_id: str):
    """Step 2: Check the progress of the 3D generation task."""
    response = requests.get(f"https://api.meshy.ai/v1/image-to-3d/{task_id}", headers=HEADERS)
    data = response.json()
    
    status = data.get("status")
    
    if status == "SUCCEEDED":
        return {"status": "success", "model_url": data["model_urls"]["glb"]}
    elif status in ["FAILED", "EXPIRED"]:
        return {"status": "failed", "error": "AI generation failed or timed out."}
    
    # Still processing
    return {"status": "processing", "progress": data.get("progress", 0)}

@app.get("/api/download-model")
def download_model(url: str):
    """Proxy the 3D model download to bypass frontend CORS blocks."""
    # The server fetches the file (no CORS restrictions here)
    res = requests.get(url)
    
    # Return the binary 3D file to the frontend
    return Response(content=res.content, media_type="model/gltf-binary")
