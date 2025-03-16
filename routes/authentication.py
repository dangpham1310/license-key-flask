from flask import Blueprint, jsonify, request
from models import Users, db,LogsHistory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,create_refresh_token
import re
from datetime import datetime
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

# Đăng ký
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Kiểm tra các trường cần thiết
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    phone = data.get("phone")

    if not all([email, password, name, phone]):
        return jsonify({"message": "Name, email, password, and phone are required"}), 400

    # Kiểm tra định dạng email
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return jsonify({"message": "Invalid email format"}), 400

    # Kiểm tra mật khẩu đủ mạnh
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long"}), 400

    # Kiểm tra số điện thoại
    if not re.match(r'^\+?[0-9]{10,15}$', phone):
        return jsonify({"message": "Invalid phone number format"}), 400

    # Kiểm tra email đã tồn tại
    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User with this email already exists"}), 400

    # Tạo người dùng mới
    new_user = Users(email=email, name=name, phone=phone)
    new_user.set_password(password)  # Hash mật khẩu
    db.session.add(new_user)

    # Tạo log
    log = LogsHistory(email = email, action="Đăng Kí Mới")
    db.session.add(log)


    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# Đăng nhập
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = Users.query.filter_by(email=email).first()

    if user and user.check_password(password):
        # Tạo access token
        user.last_login = datetime.now()

        # Tạo log
        log = LogsHistory(email = email, action="Đăng Nhập")
        db.session.add(log)
        db.session.commit()

        access_token = create_access_token(identity=user.email, expires_delta=timedelta(seconds=99999999999))
        refresh_token = create_refresh_token(identity=user.email)
        return jsonify({"access_token": access_token,"refresh_token": refresh_token}), 200
    return jsonify({"message": "Invalid credentials"}), 401



# Route yêu cầu xác thực JWT
@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Welcome {current_user}!"}), 200
