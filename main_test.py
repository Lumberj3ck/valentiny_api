from fastapi import FastAPI
from enum import Enum
from pydantic import BaseModel


app = FastAPI()


class valid_attributes(str, Enum):
    first = "first"
    second = "second"
    third = "third"


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.get("/items/only/those/{item_id}")
# we get validation here
# only values that are inside enum are valid
async def root(item_id: valid_attributes):
    print(item_id.value)
    return {"item_id": item_id}


@app.get("/item/{item_id}")
async def items_specific(
    item_id: int, short: bool, limit: int | None = None, start: int | None = None
):
    # queery parameters
    return {"item_id": item_id, "limit": limit, "start": start, "short": short}


# @app.get("/item/{item_id}")
# # validation only int value
# # otherwise we get an error
# async def items(item_id: int):
#     return {"item_id": item_id}


@app.post("/")
async def other(item: Item | None = None):
    return item
