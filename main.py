from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.saint_routes import router
from app.core.config import settings
 
from app.routers.saint_routes import router as branch_saint_router
from app.routers.saint_attendant_routes import router as saint_attendant_router
from app.routers.face_routes import router as face_router
 
app = FastAPI(title="Saint Branch API")
#ui_url = settings.UI_DOMAIN_URL
 
# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.UI_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
@app.get("/")
def root():
    return {"message": "API running successfully 🚀"}
 
# ---------------- Register Routers ----------------
app.include_router(branch_saint_router)
app.include_router(saint_attendant_router)
app.include_router(face_router)
 
# ---------------- Static Files ----------------
#app.mount("/static", StaticFiles(directory="static"), name="static")
 