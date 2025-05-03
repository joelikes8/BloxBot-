import enum
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum, Float
from sqlalchemy.orm import relationship
from database.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    discord_name = Column(String(100), nullable=False)
    roblox_username = Column(String(100))
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_staff = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    def __repr__(self):
        return f"<User(discord_id='{self.discord_id}', discord_name='{self.discord_name}')>"

class OrderState(enum.Enum):
    PENDING = "pending"
    PAYMENT_WAITING = "payment_waiting"
    PAYMENT_RECEIVED = "payment_received" 
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_number = Column(String(20), unique=True, nullable=False)
    bot_type = Column(String(100), nullable=False)
    features = Column(Text, nullable=False)
    notes = Column(Text)
    price = Column(Float, nullable=False)
    status = Column(Enum(OrderState), default=OrderState.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    status_updates = relationship("OrderStatus", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status.value}')>"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    proof_url = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, is_verified={self.is_verified})>"

class OrderStatus(Base):
    __tablename__ = "order_status"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(Enum(OrderState), nullable=False)
    comment = Column(Text)
    changed_by = Column(String(100), nullable=False)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="status_updates")
    
    def __repr__(self):
        return f"<OrderStatus(order_id={self.order_id}, status='{self.status.value}')>"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, is_read={self.is_read})>"

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_updates = Column(Boolean, default=True)
    announcements = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, order_updates={self.order_updates})>"
