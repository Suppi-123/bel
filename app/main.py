from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.operation import router as operation_router  # Ensure this line imports the router correctly
from app.database.models import init_database  # Import the init_database function

app = FastAPI()

# CORS Configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database
init_database()

app.include_router(operation_router, prefix="/api")
