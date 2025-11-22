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
#Creates items
class ItemCreate(BaseModel):
    name: str
    price: float
    description: str | None = None

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    price = Column(Float)
    description = Column(String, nullable=True)

class ItemUpdate(BaseModel):
    name: str | None
    price: float | None

class ItemDelete(BaseModel):
    id: int

#Orders
class StatusName(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    DONE = "done"

class OrderResponse(BaseModel):
    id: int
    status: StatusName
    phone_num: str | None

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(SQLEnum(StatusName), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user = relationship("User", back_populates="orders")
    phone_num = Column(String, index=True)
    def __repr__(self):
        return f"<Order(item='{self.id}', user_id='{self.user_id}')>"


#Users
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    password: str

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    email = Column(EmailStr, index=True)
    password = Column(String) #TODO: Ethan work on security measures

    orders = relationship("Order", back_populates="user")

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

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey("users.user_id"))
    reviewer_name = Column(String)
    rating = Column(Integer)
    reviewer = relationship("User", back_populates="reviews")