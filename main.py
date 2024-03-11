from fastapi import FastAPI
from .app_data import models, database
from fastapi.security import OAuth2PasswordBearer
from .routers import sections, users
 
# models.Base.metadata.drop_all(bind=database.engine)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.include_router(sections.router)
app.include_router(users.router)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# def get_user_from_token(token):
#     return User(
#         username=token + "fakedecoded", email="john@example.com", id=1
#     )
#
# def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
#     user = get_user_from_token(token)
#     return user
