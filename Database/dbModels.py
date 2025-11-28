from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from .dbConnect import Base
from enum import Enum

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

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity: float
    price: float
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    phone_num: str | None
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True


#request models for creation of orders
class OrderItemCreate(BaseModel):
    item_name: str
    quantity: int = 1

class OrderCreate(BaseModel):
    phone_num: str
    user_id: int #TODO: Ethan replace
    items: list[OrderItemCreate] = []

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(SQLEnum(OrderStatus), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user = relationship("User", back_populates="orders")
    phone_num = Column(String, index=True)
    order_items = relationship("OrderItem", back_populates="order")

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
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    password: str

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String) #TODO: Ethan work on security measures

    orders = relationship("Order", back_populates="user")
    reviews = relationship('Review', back_populates="user")
    def __repr__(self):
        return f"<User(name=' {self.name}')>"

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String) #TODO: Ethan work on security measures
    is_admin = Column(Boolean, default=True)

#Reviews
class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewer_name: str
    rating: int
    review_content: str | None

class ReviewCreate(BaseModel):
    item_id: int
    rating: int
    comment: str | None
    user_id: int  # TODO Ethan replace user_id with session/JWT auth

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer)
    comment = Column(String)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    item_id = Column(Integer, ForeignKey("items.id"))

    user = relationship("User", back_populates="reviews")
    item = relationship("Item", back_populates="reviews")