from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel
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

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(SQLEnum(StatusName), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order(item='{self.id}', user_id='{self.user_id}')>"

#Users
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
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