from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from Database.dbModels import *
from Database.dbConnect import dbSession, engine, Base
from starlette import status
from tests.seed import seed_database
import logging
from owner.admin import setup_admin

Base.metadata.create_all(bind=engine)
app = FastAPI(title="J-Bites")
setup_admin(app)

@app.on_event("startup")
def reset_database():
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    Base.metadata.create_all(bind=engine)  # Recreate fresh
    seed_database()
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

@app.post("/reviews", status_code=201, response_model=ReviewResponse)
def create_review(review_data, session: dbSession):
    #sends to the DB a review that is pending and through /admin the admin will change
    review = Review(
        item_id=review_data.review_id,
        rating=review_data.rating,
        comment=review_data.comment,
        user_id=review_data.user_id,
        status=ReviewStatus.PENDING,
    )

    session.add(review)
    session.commit()
    return {"message": "Review created and submitted for approval.", "review": review.id}

#shows approved reviews
@app.get("/items/{item_id}/reviews")
def get_reviews(item_id: int, session: dbSession):
    #gets reviews based on id and approved status
    reviews = session.query(Review).filter(
        Review.item_id == item_id,
        Review.status == ReviewStatus.APPROVED
    ).all()
    return reviews

@app.post("/orders", status_code=201, response_model=OrderResponse)
def create_order(order_data: OrderCreate, session: dbSession):

    order = Order(
        status = OrderStatus.PENDING,
        phone_num = order_data.phone_num,
        user_id = order_data.user_id,
    )
    session.add(order)
    session.flush()

    total_price = 0
    for i_data in order_data.items:
        order_item = OrderItem(
            order_id = order.id,
            item_id = i_data.item_id,
            quantity = i_data.quantity,
        )
        session.add(order_item)
        total_price += i_data.price * i_data.quantity
    session.commit()
    session.refresh(order)

    return order

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: dbSession):
    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items_response = []
    for o_item in order.order_items:
        items_response.append({
            "id": o_item.item_id,
            "quantity": o_item.quantity,
            "item_name": o_item.item_name,
            "item_id": o_item.item_id,
            "price": o_item.price
        })

    return {
        "id": order.id,
        "status": order.status.value,
        "phone_num": order.phone_num,
        "items": items_response
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)