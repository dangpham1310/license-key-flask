import uuid
from flask import Blueprint, jsonify, request
from models import Users, db, License, SubLicenseKey,DeviceUsage, LogsHistory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re
import random
import string
from datetime import datetime, timedelta
from datetime import datetime
import pytz


license_bp = Blueprint('license_routes', __name__)

@license_bp.route('/create', methods=['POST'])
@jwt_required()
def create_license():
    email = get_jwt_identity()
    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()

    # Kiểm tra gói license hợp lệ
    package = data.get("package")
    if package not in ["6_months", "12_months", "36_months", "lifetime", "0_months"]:
        return jsonify({"message": "Invalid package. Choose from '6_months', '12_months', '36_months', 'lifetime', '0_months'."}), 400

    # Xác định số lượng camera
    camera_count_map = {
        "6_months": 8,
        "12_months": 16,
        "36_months": 32,
        "lifetime": 64,
    }
    camera_count = camera_count_map.get(package, 0)

    # Tạo license key ngẫu nhiên với UUID
    license_key = str(uuid.uuid4())

    # Thời gian hiện tại UTC
    issued_date = datetime.utcnow()
    
    # Tính toán ngày hết hạn
    if package == "lifetime":
        expiry_date = None
    else:
        months = int(package.split('_')[0])  # Lấy số tháng từ package
        expiry_date = issued_date + timedelta(days=months * 30)  # Giả định mỗi tháng có 30 ngày

    # Chuyển múi giờ sang GMT+7
    gmt7 = pytz.timezone('Asia/Bangkok')

    # Đảm bảo issued_date có timezone UTC
    if issued_date.tzinfo is None:
        issued_date = pytz.utc.localize(issued_date)

    # Chuyển issued_date sang GMT+7
    issued_date_gmt7 = issued_date.astimezone(gmt7)

    # Mapping package sang tiếng Việt
    package_mapping = {
        "6_months": "6 Tháng",
        "12_months": "12 Tháng",
        "36_months": "36 Tháng",
        "lifetime": "Vĩnh Viễn"
    }
    package_vietnamese = package_mapping.get(package, "Không Xác Định")

    # Tạo License mới
    new_license = License(
        user_id=user.id,
        license_key=license_key,
        status="InActive",
        issued_date=issued_date,
        expiry_date=expiry_date,
        package=package,
        camera_count=camera_count,
        history=[{
            "action": "Khởi Tạo",
            "date": issued_date_gmt7.strftime('%H:%M %d-%m-%Y'),
            "details": f"{package_vietnamese}"
        }]
    )

    # Thêm 3 `SubLicenseKey` với các function khác nhau
    functions = ["time", "camera", "duty"]
    for func in functions:
        print(func)
        sub_key = SubLicenseKey(
            license=new_license,  # Gán license
            sub_license_key=str(uuid.uuid4()),  # Key ngẫu nhiên bằng UUID
            function=func
        )
        db.session.add(sub_key)  # Thêm vào session

    db.session.add(new_license)  # Thêm license
    db.session.commit()  # Lưu vào database

    return jsonify({
        "message": "License created successfully",
        "license_key": license_key,
        "package": package,
        "camera_count": camera_count,
        "expiry_date": expiry_date.strftime('%H:%M %d-%m-%Y') if expiry_date else "Vĩnh Viễn",
        "sub_license_keys": [sub.sub_license_key for sub in new_license.sub_licenses]  # Trả về danh sách SubLicenseKey
    }), 201


# Lấy Danh Sách License Key cấp 1 theo tài khoản
@license_bp.route('/list', methods=['GET'])
@jwt_required()
def list_licenses():
    email = get_jwt_identity()
    user_id = Users.query.filter_by(email=email).first().id
    licenses = License.query.filter_by(user_id=user_id).all()
    license_list = [{
        "id": license.id,
        "license_key": license.license_key,
        # "status": license.status,
        # "issued_date": license.issued_date.isoformat() if license.issued_date else None,
        # "expiry_date": license.expiry_date.isoformat() if license.expiry_date else None,
        "package": license.package,
    } for license in licenses]

    return jsonify({"licenses": license_list}), 200

@license_bp.route('/delete/<int:license_id>', methods=['DELETE'])
@jwt_required()
def delete_license(license_id):
    email = get_jwt_identity()
    user_id = Users.query.filter_by(email=email).first().id

    license_to_delete = License.query.filter_by(id=license_id, user_id=user_id).first()

    if not license_to_delete:
        return jsonify({"message": "License not found or you don't have permission to delete it."}), 404

    db.session.delete(license_to_delete)
    db.session.commit()

    return jsonify({"message": f"License with ID {license_id} deleted successfully."}), 200

# Check key cấp 1 và trả về 3 key cấp 2
@license_bp.route('/level-two-license/<string:license_key>', methods=['GET'])
@jwt_required()
def get_license_level2(license_key):
    license = License.query.filter_by(license_key=license_key).first()
    if not license:
        return jsonify({"message": "License not found"}), 404

    # Lấy danh sách SubLicenseKey và function
    sub_license_data = [
        {
            "sub_license_key": sub.sub_license_key,
            "function": sub.function
        }
        for sub in license.sub_licenses
    ]

    return jsonify({
        "license_key": license.license_key,
        "status": license.status,
        "sub_license_keys": sub_license_data
    }), 200



# Kiểm tra license key cấp 2
@license_bp.route('/check/<string:license>/<string:func>', methods=['GET'])
@jwt_required()
def check_license(license,func):
    if func == "time":
        sub_license = SubLicenseKey.query.filter_by(sub_license_key=license, function="time").first()
        if not sub_license:
            return jsonify({"message": "Sub License not found"}), 404
        parent_license = License.query.filter_by(id=sub_license.license_id).first()
        if not parent_license:
            return jsonify({"message": "Parent License not found"}), 404
        sub_license.last_used = datetime.now()
        db.session.commit()
        return jsonify({
            "package": parent_license.package,
            "expiry_date": parent_license.expiry_date.isoformat() if parent_license.expiry_date else "Vĩnh Viễn",
            "status": parent_license.status
        }), 200

    elif func == "camera":
        sub_license = SubLicenseKey.query.filter_by(sub_license_key=license, function="camera").first()
        if not sub_license:
            return jsonify({"message": "Sub License not found"}), 404
        parent_license = License.query.filter_by(id=sub_license.license_id).first()
        if not parent_license:
            return jsonify({"message": "Parent License not found"}), 404
        sub_license.last_used = datetime.now()
        db.session.commit()
        return jsonify({
            "license_key": parent_license.license_key,
            "package": parent_license.package,
            "camera_count": parent_license.camera_count,
            "status": parent_license.status,
            "camera_used": parent_license.camera_used
        }), 200
    elif func == "duty":
        sub_license = SubLicenseKey.query.filter_by(sub_license_key=license, function="duty").first()
        if not sub_license:
            return jsonify({"message": "Sub License not found"}), 404
        parent_license = License.query.filter_by(id=sub_license.license_id).first()
        if not parent_license:
            return jsonify({"message": "Parent License not found"}), 404
        sub_license.last_used = datetime.now()
        db.session.commit()
        return jsonify({
            "Check":"Nhờ Anh Tấn nói lại tại em quên rồi"
        }), 200
    else:
        return jsonify({"message": "Invalid function"}), 400





@license_bp.route('/update-camera-usage/<string:sub_license_key>', methods=['POST'])
@jwt_required()
def update_camera_usage(sub_license_key):
    """
    Cập nhật số camera đã sử dụng cho một máy cụ thể thông qua SubLicenseKey (function="camera").
    """
    data = request.get_json()
    device_id = data.get("device_id")  # UUID hoặc MAC Address của máy
    camera_count = data.get("camera_count")  # Số camera đang sử dụng
    print("device_id: ",device_id)
    if not device_id or camera_count is None:
        return jsonify({"message": "Missing device_id or camera_count"}), 400

    # Tìm `SubLicenseKey` với function là "camera"
    sub_license = SubLicenseKey.query.filter_by(sub_license_key=sub_license_key, function="camera").first()
    if not sub_license:
        return jsonify({"message": "SubLicenseKey not found or not for function 'camera'"}), 404

    # Truy xuất License cấp 1 từ SubLicenseKey
    license = sub_license.license
    if not license:
        return jsonify({"message": "Parent License not found"}), 404

    # Kiểm tra nếu số camera vượt quá giới hạn của License
    # print("license.camera_used: ",license.camera_used)
    # print("camera_count: ",camera_count)

    # Kiểm tra xem máy này đã tồn tại trong DeviceUsage chưa
    device_usage = DeviceUsage.query.filter_by(license_id=license.id, device_id=device_id).first()

    if device_usage:
        if int(camera_count) > license.camera_count:
            return jsonify({"message": "Exceeded camera limit"}), 403
        device_usage.camera_count = camera_count
        device_usage.last_updated = datetime.utcnow()
    else:
        # Tạo mới bản ghi nếu máy chưa được đăng ký
        if license.camera_used + int(camera_count) > license.camera_count:
            return jsonify({"message": "Exceeded camera limit"}), 403
        device_usage = DeviceUsage(
            license_id=license.id,
            device_id=device_id,
            camera_count=camera_count,
            last_updated=datetime.utcnow()
        )
        db.session.add(device_usage)

    # Cập nhật tổng số camera đang được sử dụng trong License
    total_cameras_used = db.session.query(db.func.sum(DeviceUsage.camera_count)).filter_by(license_id=license.id).scalar() or 0
    license.camera_used = total_cameras_used

    logs_history = LogsHistory(email = license.user.email, action="Cập Nhật Camera Đang Sử Dụng")
    
    db.session.add(logs_history)
    db.session.commit()
    
    return jsonify({
        "message": "Camera usage updated successfully",
        "total_cameras_used": license.camera_used,  # Tổng số camera đã dùng
        "camera_limit": license.camera_count  # Giới hạn camera của License
    }), 200


