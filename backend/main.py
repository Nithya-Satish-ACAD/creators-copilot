from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import generate, revise
from routes.upload import router as upload_router

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(generate.router)
app.include_router(revise.router)
app.include_router(upload_router) 
