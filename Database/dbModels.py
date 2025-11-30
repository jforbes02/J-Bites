from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, ForeignKey, Boolean, DateTime, event
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel, EmailStr, Field
from .dbConnect import Base
from enum import Enum
from owner.notifications import notify_order_ready, notify_order_cancelled

#Items
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    description: str | None = None

    class Config:
        from_attributes = True


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    price = Column(Float)
    description = Column(String, nullable=True)

    reviews = relationship("Review", back_populates="item")
    order_items = relationship("OrderItem", back_populates="item")

#Orders
class OrderStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    DONE = "done"
    CANCEL_REQUEST = "cancel_request"

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity: int
    price: float
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    phone_num: str | None
    items: list[OrderItemResponse] = []
    total_price: float
    username: str
    user_id: int

    class Config:
        from_attributes = True


#request models for creation of orders
class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(ge=1, le=100)

class OrderCreate(BaseModel):
    phone_num: str
    username: str
    items: list[OrderItemCreate]

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(SQLEnum(OrderStatus), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user = relationship("User", back_populates="orders")
    phone_num = Column(String, index=True)
    order_items = relationship("OrderItem", back_populates="order")

    cancelled_at = Column(DateTime, nullable=True)
    stripe_session_id = Column(String, nullable=True)  # Stripe checkout session
    payment_status = Column(String, default="pending")  # pending, paid, refunded

    def __repr__(self):
        return f"<Order(item='{self.id}', user_id='{self.user_id}')>"


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price_at_order = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_items")
    item = relationship("Item", back_populates="order_items")

#Users
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    name: str
    email: EmailStr

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    email = Column(String,unique=True, index=True)
    password = Column(String)

    orders = relationship("Order", back_populates="user")
    reviews = relationship('Review', back_populates="user")

    def __repr__(self):
        return f"<User(name=' {self.name}')>"

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    password = Column(String)
    is_admin = Column(Boolean, default=True)

#Reviews
class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewer_name: str
    rating: int = Field(ge=1, le=5)
    review_content: str | None

class ReviewCreate(BaseModel):
    item_id: int
    rating: int
    comment: str | None
    username: str

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer, )
    comment = Column(String)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    item_id = Column(Integer, ForeignKey("items.id"))

    user = relationship("User", back_populates="reviews")
    item = relationship("Item", back_populates="reviews")


@event.listens_for(Order, "before_update")
def send_sms_on_change(mapper, connection, target):
    #gets session
    session = Session.object_session(target)

    old_order = session.query(Order).filter(Order.id == target.id).first()

    if old_order:
        old_status = old_order.status
        new_status = target.status

        if old_status != new_status:
            if new_status == OrderStatus.DONE:
                print(f"📱 Sending 'ready' SMS for order #{target.id}")
                notify_order_ready(target.phone_num, target.id)
            elif new_status == OrderStatus.CANCELLED:
                print(f"📱 Sending 'cancelled' SMS for order #{target.id}")
                notify_order_cancelled(target.phone_num, target.id)
