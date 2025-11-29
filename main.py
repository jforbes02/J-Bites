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
        db_item = session.query(Item).filter(Item.id == i_data.item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")

        order_item = OrderItem(
            order_id = order.id,
            item_id = i_data.item_id,
            quantity = i_data.quantity,
            price_at_order=db_item.price
        )
        session.add(order_item)
        total_price += db_item.price * i_data.quantity
    session.commit()
    session.refresh(order)

    #building the apis response
    items_response = []
    for o_item in order.order_items:
        items_response.append(
            OrderItemResponse(
                id=o_item.id,
                item_id=o_item.item_id,
                item_name=o_item.item.name,
                quantity=o_item.quantity,
                price=o_item.price_at_order
            )
        )

    return OrderResponse(
            id = order.id,
            status = order.status,
            phone_num = order.phone_num,
            items=items_response,
            total_price=total_price
    )


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: dbSession):
    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items_response = []
    total_price = 0
    for o_item in order.order_items:
        items_response.append(
            OrderItemResponse(
                id=o_item.id,
                item_id=o_item.item_id,
                item_name=o_item.item.name,  # Now this works with eager loading!
                quantity=o_item.quantity,
                price=o_item.price_at_order
            )
        )
        total_price += o_item.price_at_order * o_item.quantity  # ✅ FIXED: Moved inside loop

    return OrderResponse(
        id = order.id,
        status = order.status,
        phone_num = order.phone_num,
        items=items_response,
        total_price=total_price

    )

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, session: dbSession):
    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot cancel completed order. Please contact support for refunds")
    if order.status == OrderStatus.DONE:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed order. Please contact support for refunds."
        )
    #TODO add Stripe refund logic
    try:
        session.delete(order)
        session.commit()
        session.refresh(order)
        return {"message": "Order canceled.", "order": order.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Cancellation Failed: {str(e)}")

@app.get("/orders/search/{phone_num}", response_model=List[OrderResponse])
def get_order_by_phone(phone_num: str, session: dbSession):
    orders = session.query(Order).filter(Order.phone_num == phone_num).all()
    if not orders:
        raise HTTPException(status_code=404, detail="Order not found")
    response = []

    for order in orders:
        items_response = []
        total_price = 0

        for o_item in order.order_items:
            items_response.append(
                OrderItemResponse(
                    id=o_item.id,
                    item_id=o_item.item_id,
                    item_name=o_item.item.name,
                    quantity=o_item.quantity,
                    price=o_item.price_at_order
                )
            )
            total_price += o_item.price_at_order * o_item.quantity

        response.append(
            OrderResponse(
                id=order.id,
                status=order.status,
                phone_num=order.phone_num,
                items=items_response,
                total_price=total_price,
            )
        )

    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)