from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from Database.dbModels import Item, ItemResponse
from Database.dbConnect import dbSession, engine, Base
from starlette import status
import logging
from owner.admin import setup_admin

Base.metadata.create_all(bind=engine)
app = FastAPI(title="J-Bites")
setup_admin(app)

@app.on_event("startup")
def reset_database():
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    Base.metadata.create_all(bind=engine)  # Recreate fresh
    logging.basicConfig(level=logging.INFO)
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, session: dbSession):
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/items", response_model=List[ItemResponse])
def get_all_items(session: dbSession):
    items = session.query(Item).all()
    return items


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)