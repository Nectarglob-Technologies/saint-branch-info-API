from fastapi import FastAPI
from app.routers.saint_routes import router as branch_saint_router
from app.routers.saint_attendant_routes import router as saint_attendant_router
from app.routers.face_routes import router as face_router
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Saint Branch API")

@app.get("/")
def root():
    print("API is running successfully 🚀")
    return {"message": "API running successfully 🚀"}

# ---------------- Register Routers ----------------

app.include_router(branch_saint_router)
app.include_router(saint_attendant_router)
app.include_router(face_router)



app.mount("/static", StaticFiles(directory="static"), name="static")

