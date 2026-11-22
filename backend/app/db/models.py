from datetime import datetime, date
from sqlalchemy import (String, Integer, Float, Date, DateTime, ForeignKey,
                        Text, Boolean, JSON, create_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


def col(t=String, **kw):
    return mapped_column(t, **kw)


# ---------- 15 business tables required by the spec ----------
class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()
    email: Mapped[str] = col()
    phone: Mapped[str] = col()
    city: Mapped[str] = col()
    region: Mapped[str] = col()
    customer_type: Mapped[str] = col()


class Seller(Base):
    __tablename__ = "sellers"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()
    rating: Mapped[float] = col(Float)
    approval_status: Mapped[str] = col()


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()
    category: Mapped[str] = col()
    price: Mapped[float] = col(Float)
    warranty_months: Mapped[int] = col(Integer)
    return_window_days: Mapped[int] = col(Integer)
    seller_id: Mapped[str] = col(ForeignKey("sellers.id"))


class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()
    region: Mapped[str] = col()


class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = col(ForeignKey("products.id"))
    warehouse_id: Mapped[str] = col(ForeignKey("warehouses.id"))
    quantity: Mapped[int] = col(Integer)


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = col(primary_key=True)
    customer_id: Mapped[str] = col(ForeignKey("customers.id"))
    order_date: Mapped[date] = col(Date)
    status: Mapped[str] = col()
    total_amount: Mapped[float] = col(Float)
    seller_id: Mapped[str] = col(ForeignKey("sellers.id"))
    warehouse_id: Mapped[str] = col(ForeignKey("warehouses.id"))


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = col(ForeignKey("orders.id"))
    product_id: Mapped[str] = col(ForeignKey("products.id"))
    quantity: Mapped[int] = col(Integer)
    price: Mapped[float] = col(Float)


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[str] = col(primary_key=True)
    order_id: Mapped[str] = col(ForeignKey("orders.id"))
    partner_id: Mapped[str] = col(ForeignKey("delivery_partners.id"))
    tracking_no: Mapped[str] = col()
    status: Mapped[str] = col()
    region: Mapped[str] = col()
    shipped_date: Mapped[date] = col(Date)
    expected_date: Mapped[date] = col(Date)
    delivered_date: Mapped[date] = col(Date, nullable=True)
    delay_reason: Mapped[str] = col(nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = col(primary_key=True)
    order_id: Mapped[str] = col(ForeignKey("orders.id"))
    method: Mapped[str] = col()
    status: Mapped[str] = col()
    amount: Mapped[float] = col(Float)
    paid_at: Mapped[datetime] = col(DateTime)


class Return(Base):
    __tablename__ = "returns"
    id: Mapped[str] = col(primary_key=True)
    order_id: Mapped[str] = col(ForeignKey("orders.id"))
    product_id: Mapped[str] = col(ForeignKey("products.id"))
    reason: Mapped[str] = col()
    status: Mapped[str] = col()
    requested_at: Mapped[date] = col(Date)


class Refund(Base):
    __tablename__ = "refunds"
    id: Mapped[str] = col(primary_key=True)
    order_id: Mapped[str] = col(ForeignKey("orders.id"))
    return_id: Mapped[str] = col(ForeignKey("returns.id"), nullable=True)
    amount: Mapped[float] = col(Float)
    status: Mapped[str] = col()
    initiated_at: Mapped[date] = col(Date)
    processed_at: Mapped[date] = col(Date, nullable=True)
    delay_reason: Mapped[str] = col(nullable=True)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = col(primary_key=True)
    name: Mapped[str] = col()
    team: Mapped[str] = col()


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[str] = col(primary_key=True)
    customer_id: Mapped[str] = col(ForeignKey("customers.id"))
    order_id: Mapped[str] = col(ForeignKey("orders.id"), nullable=True)
    category: Mapped[str] = col()
    description: Mapped[str] = col(Text)
    severity: Mapped[str] = col()
    created_at: Mapped[date] = col(Date)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id: Mapped[str] = col(primary_key=True)
    customer_id: Mapped[str] = col(ForeignKey("customers.id"))
    order_id: Mapped[str] = col(ForeignKey("orders.id"), nullable=True)
    agent_id: Mapped[str] = col(ForeignKey("agents.id"))
    subject: Mapped[str] = col()
    status: Mapped[str] = col()
    priority: Mapped[str] = col()
    created_at: Mapped[datetime] = col(DateTime)
    resolved_at: Mapped[datetime] = col(DateTime, nullable=True)
    first_contact_resolved: Mapped[bool] = col(Boolean, default=False)


# ---------- App tables (auth, docs, logs, chat, feedback) ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = col(unique=True)
    password_hash: Mapped[str] = col()
    role: Mapped[str] = col()


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = col()
    doc_type: Mapped[str] = col()
    policy_name: Mapped[str] = col(nullable=True)
    version: Mapped[str] = col(default="1")
    effective_date: Mapped[date] = col(Date, nullable=True)
    is_active: Mapped[bool] = col(Boolean, default=True)
    meta: Mapped[dict] = col(JSON, default=dict)


class ParentChunk(Base):
    __tablename__ = "parent_chunks"
    id: Mapped[str] = col(primary_key=True)
    document_id: Mapped[int] = col(ForeignKey("documents.id"))
    section: Mapped[str] = col(nullable=True)
    page: Mapped[int] = col(Integer, nullable=True)
    text: Mapped[str] = col(Text)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = col(index=True)
    user_id: Mapped[int] = col(Integer)
    role: Mapped[str] = col()
    content: Mapped[str] = col(Text)
    sources: Mapped[dict] = col(JSON, nullable=True)
    created_at: Mapped[datetime] = col(DateTime, default=datetime.utcnow)


class QueryLog(Base):
    __tablename__ = "query_logs"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = col(Integer, nullable=True)
    query: Mapped[str] = col(Text)
    intent: Mapped[str] = col(nullable=True)
    retrieved_docs: Mapped[dict] = col(JSON, nullable=True)
    sql_queries: Mapped[dict] = col(JSON, nullable=True)
    response: Mapped[str] = col(Text, nullable=True)
    error: Mapped[str] = col(Text, nullable=True)
    latency_ms: Mapped[int] = col(Integer, nullable=True)
    created_at: Mapped[datetime] = col(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = col(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = col(Integer)
    rating: Mapped[int] = col(Integer)
    comment: Mapped[str] = col(Text, nullable=True)

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)