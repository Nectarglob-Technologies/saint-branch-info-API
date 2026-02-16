from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.saint_routes import router
 
 
from app.routers.saint_routes import router as branch_saint_router
from app.routers.saint_attendant_routes import router as saint_attendant_router
from app.routers.face_routes import router as face_router
from app.core.config import settings
 
app = FastAPI(title="Saint Branch API")
print(f"UI Origin value:  {settings.UI_ORIGINS}")  # Debug print to verify the value is loaded correctly

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.UI_ORIGINS,  # ✅ SMART CONFIG
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ---------------- Health Check ----------------
@app.get("/")
def root():
    return {
        "message": "API running successfully 🚀",
        #"environment": settings.ENVIRONMENT
    }
 
# ---------------- Register Routers ----------------
app.include_router(branch_saint_router)
app.include_router(saint_attendant_router)
app.include_router(face_router)
 
# ---------------- Static Files ----------------
app.mount("/static", StaticFiles(directory="static"), name="static")
 