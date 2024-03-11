from fastapi import FastAPI
from .app_data import models, database
from .routers import sections, users
 
#models.Base.metadata.drop_all(bind=database.engine)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.include_router(sections.router)
app.include_router(users.router)

