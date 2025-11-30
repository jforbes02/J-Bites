from typing import List
import stripe
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from sqladmin.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from starlette.responses import RedirectResponse
from config.config import settings
from Database.dbModels import *
from Database.dbConnect import dbSession, engine, Base
from tests.seed import seed_database
import logging
from owner.admin import setup_admin
from owner.notifications import notify_order_confirmed, send_sms
from middleware.auth_middleware import auth_middleware
from middleware.security import hash_password, verify_password, create_access_token, get_current_user, get_current_admin
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from owner.payments import StripeService
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
load_dotenv()
settings.validate()
app = FastAPI(title="J-Bites")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.middleware("http")(auth_middleware)

# for frontend folder  ---------
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("frontend/templates/index.html") as f:
        return f.read()
@app.get("/login.html", response_class=HTMLResponse)
async def login_page():
    with open("frontend/templates/login.html") as f:
       return f.read()

@app.get("/register.html", response_class=HTMLResponse)
async def register_page():
    with open("frontend/templates/register.html") as f:
       return f.read()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "enviornment": settings.ENVIRONMENT,
        "auth_enabled": not (settings.DISABLE_AUTH and settings.is_development())
    }
setup_admin(app)

CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]
@app.on_event("startup")
def reset_database():
    Base.metadata.create_all(engine)
    if os.getenv("SEED_DATABASE", "false").lower() == "true":
        seed_database()
        Base.metadata.create_all(engine)

    logging.basicConfig(level=logging.INFO)

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
def create_review(review_data: ReviewCreate, current_user: CurrentUser, session: dbSession):
    #sends to the DB a review that is pending and through /admin the admin will change
    review = Review(
        item_id=review_data.item_id,
        rating=review_data.rating,
        comment=review_data.comment,
        user_id=current_user.user_id,
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
def create_order(order_data: OrderCreate, current_user: CurrentUser, session: dbSession):
    order = Order(
        status = OrderStatus.PENDING,
        phone_num = order_data.phone_num,
        user_id = current_user.user_id,  # Use the looked-up user_id
        payment_status="pending"
    )
    session.add(order)
    session.flush()

    stripe_items = []
    total_price = 0
    for i_data in order_data.items:
        db_item = session.query(Item).filter(Item.id == i_data.item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail=f"Item with id {i_data.item_id} not found")

        order_item = OrderItem(
            order_id = order.id,
            item_id = i_data.item_id,
            quantity = i_data.quantity,
            price_at_order=db_item.price
        )
        session.add(order_item)
        stripe_items.append({
            'name': db_item.name,
            'quantity': i_data.quantity,
            'price': db_item.price
        })
        total_price += db_item.price * i_data.quantity
    session.commit()

    try:
        checkout_url = StripeService.create_checkout(
            order_id=order.id,
            items=stripe_items,
            phone=order.phone_num,
            success_url=f"http://localhost:8000/payment-success?order_id={order.id}",
            cancel_url=f"http://localhost:8000/payment-cancelled?order_id={order.id}"
        )
        return {
            "order_id": order.id,
            "checkout_url": checkout_url,
            "total": total_price,
            "message": "Order created. Redirecting to payment..."
        }
    except Exception as e:
        session.delete(order)
        session.commit()
        raise HTTPException(status_code=500, detail=f"Payment setup failure")




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
                item_name=o_item.item.name,
                quantity=o_item.quantity,
                price=o_item.price_at_order
            )
        )
        total_price += o_item.price_at_order * o_item.quantity

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

    if order.status == OrderStatus.DONE:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed order. Please contact support for refunds."
        )
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="already cancelled order.")


    order.payment_status = OrderStatus.CANCEL_REQUEST
    order.cancelled_at = datetime.now()
    if order.payment_status == "paid":
        message = f"📋 J-Bites: Cancellation request for order #{order.id} received. Refund pending admin approval."
    else:
        message = f"📋 J-Bites: Order #{order.id} cancellation request received."
    if settings.ENABLE_SMS:
        send_sms(order.phone_num, message)

    try:
        session.commit()
        return {"message": "Cancellation request sent, Admin will review and process refund",
                "order_id": order.id,
                "paayment_status": order.payment_status
                }
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

@app.post("/login")
def login(user: UserCreate, db: dbSession):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: dbSession):
    existing = db.query(User).filter(User.name == user.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists")
    new_user = User(
        email=user.email,
        name=user.name,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse(
        name=new_user.name,
        email=new_user.email
    )

@app.post("/admin/login")
def admin_login(email: str, password: str, db: dbSession):
    admin = db.query(Admin).filter(Admin.email == email).first()

    if not admin or not verify_password(password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": admin.email, "is_admin": True})
    return {"access_token": token, "token_type": "bearer", "is_admin": True, "redirect_url": "/admin"}


@app.get("/admin/orders/pending-cancellations", response_model=List[OrderResponse])
def get_pending_cancellations(current_admin: CurrentAdmin, db: dbSession):
    """Get all orders with cancellation requests - admin only"""

    orders = db.query(Order).filter(Order.status == OrderStatus.CANCELLATION_REQUESTED).all()

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
                username=order.user.name,
                user_id=order.user_id,
                payment_status=order.payment_status
            )
        )

    return response
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: dbSession):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.getenv("SECRET_WEBHOOK")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event['data']['object']
        order_id = session['metadata']['order_id']

        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.payment_status = order.payment_status = "paid"
            order.stripe_session_id = session['id']
            db.commit()

            notify_order_confirmed(order.phone_num, order.id, session['amount_total']/100)
    return {"status": "success"}

@app.get("/payment-success")
async def payment_success(order_id: int):
    return RedirectResponse(url="/?success=true")

@app.get("/payment-cancelled")
async def payment_cancelled(order_id: int, db: dbSession):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return RedirectResponse(url="/?cancelled=true")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
