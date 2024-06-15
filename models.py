from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime


db = SQLAlchemy()


class SenderTypeForMessage(enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    
class SenderTypeForNotice(enum.Enum):
    BOSS = "boss"
    STAFF = "staff"

# 고객 테이블
class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(50), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    chargeTime = db.Column(db.DateTime, nullable=True)

# 직원 테이블
class Staff(db.Model):
    __tablename__ = 'staff'
    staff_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(50), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)

# 사장 테이블
class Boss(db.Model):
    __tablename__ = 'boss'
    boss_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(50), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)

# 메시지 테이블
class Message(db.Model):
    __tablename__ = 'message'
    message_id = db.Column(db.Integer, primary_key=True)
    sender_type = db.Column(db.Enum(SenderTypeForMessage), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    recipient_type = db.Column(db.Enum(SenderTypeForMessage), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 주문 테이블
class Order(db.Model):
    __tablename__ = 'order'
    order_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.menu_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 공지사항 테이블
class Notice(db.Model):
    __tablename__ = 'notice'
    notice_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_type = db.Column(db.Enum(SenderTypeForNotice), nullable=False)
    author_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

# 메뉴 테이블
class Menu(db.Model):
    __tablename__ = 'menu'
    menu_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # 이미지 URL을 저장할 필드 추가