from fastapi import FastAPI
from .routers import sections, users, aws_interaction, domain
from .app_data import models, database, crud
from fastapi.middleware.cors import CORSMiddleware



origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://www.my-valentine-postcard.site",
    "https://postcard-api.24-7.ro/",
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
app.include_router(aws_interaction.router)
app.include_router(domain.router)


@app.on_event("startup")
async def startup_event():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        crud.init_data(db)
    finally:
        db.close()