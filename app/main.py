from fastapi import FastAPI
from .routers import sections, users
from .app_data import models, database
from fastapi.middleware.cors import CORSMiddleware
 
# models.Base.metadata.drop_all(bind=database.engine)
models.Base.metadata.create_all(bind=database.engine)

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://www.my-valentine-postcard.site",
    "https://postcard-api.24-7.ro/"
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sections.router)
app.include_router(users.router)

