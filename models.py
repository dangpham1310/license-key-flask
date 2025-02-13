from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')  # Default role is 'user'
    licenses = db.relationship('License', backref='user', lazy=True)  # Quan hệ 1-n với License
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)



class License(db.Model):
    __tablename__ = 'licenses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_key = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(50), nullable=False, default='UnActive')
    issued_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    package = db.Column(db.String(50), nullable=False)
    camera_count = db.Column(db.Integer, nullable=False, default=0)
    camera_used = db.Column(db.Integer, nullable=False, default=0)
    history = db.Column(db.JSON, nullable=False, default=[])
    
    # Quan hệ 1-n với SubLicenseKey
    sub_licenses = db.relationship('SubLicenseKey', backref='license', lazy=True, cascade="all, delete-orphan")

class SubLicenseKey(db.Model):
    __tablename__ = 'sub_license_keys'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    license_id = db.Column(db.Integer, db.ForeignKey('licenses.id'), nullable=False)
    sub_license_key = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    last_used = db.Column(db.DateTime, nullable=True)
    function = db.Column(db.String(50), nullable=False)

class DeviceUsage(db.Model):
    __tablename__ = 'device_usage'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    license_id = db.Column(db.Integer, db.ForeignKey('licenses.id'), nullable=False)
    device_id = db.Column(db.String(255), nullable=False)  # Mã định danh máy (ví dụ: MAC Address, UUID)
    camera_count = db.Column(db.Integer, nullable=False, default=0)  # Số camera đang dùng trên máy này
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Liên kết với License
    license = db.relationship('License', backref='device_usages', lazy=True)





class LogsHistory(db.Model):
    __tablename__ = 'logs_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    permissions = db.Column(db.JSON, nullable=False, default=[])  # Lưu trữ danh sách quyền

