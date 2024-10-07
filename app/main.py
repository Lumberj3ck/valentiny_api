from fastapi import FastAPI
from .routers import checkout, sections, users, aws_interaction, domain
from .app_data import models, database, crud
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from pathlib import Path
import os
dotenv_path = Path("app/.env.api")
load_dotenv(dotenv_path=dotenv_path)

origins = os.getenv('ORIGINS')
origins = origins.split(',')

app = FastAPI(docs_url=None, redoc_url=None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sections.router)
app.include_router(users.router)
app.include_router(aws_interaction.router)
app.include_router(domain.router)
app.include_router(checkout.router)


@app.on_event("startup")
async def startup_event():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        crud.init_data(db)
    finally:
        db.close()