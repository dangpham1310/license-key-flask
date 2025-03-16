from flask import Blueprint, current_app, flash, jsonify, request, render_template, redirect, session
from models import DutyFunction, SubLicenseKey, Users, db, License,Role, LogsHistory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm.attributes import flag_modified




admin_bp = Blueprint('admin_routes', __name__)



def check_admin():
    if session.get('logged_in') and session.get('role') == "Admin":
        return True
    return False

@admin_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('admin/pages-sign-in.html')
    email = request.form.get('email')
    password = request.form.get('password')
    user = Users.query.filter_by(email=email).first()
    if not user or user.role != "Admin":
        return jsonify({"message": "You are not authorized to access this route"}), 403

    if user and user.check_password(password):
        session['email'] = email
        session['role'] = "Admin"
        session['logged_in'] = True
        return redirect('/admin/dashboard')
    return jsonify({"message": "Invalid credentials"}), 401

@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if check_admin() == False:
        return redirect('/admin/users')
    return render_template('admin/index.html')

@admin_bp.route('/users', methods=['GET'])
def get_users():
    print(check_admin())
    if check_admin() == False:
        return redirect('/admin/login')
    users = Users.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/licenses/<int:user_id>', methods=['GET'])
def licenses_admin(user_id):
    if check_admin() == False:
        return redirect('/admin/login')

    # Lấy danh sách license theo `user_id`
    licenses = License.query.filter_by(user_id=user_id).all()

    # Trả về template với danh sách license
    return render_template('admin/license.html', licenses=licenses, user_id=user_id)

@admin_bp.route('/licenses/<int:license_id>/change-key', methods=['POST'])
def change_license_key(license_id):
    # Kiểm tra quyền admin
    if not check_admin():
        return jsonify({"error": "Unauthorized"}), 401

    license = License.query.get(license_id)
    if not license:
        return jsonify({"error": "License not found"}), 404

    # Tạo khóa mới
    new_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
    license.license_key = new_key

    # Lấy thời gian hiện tại theo GMT+7
    gmt7_time = datetime.utcnow() + timedelta(hours=7)

    # Đảm bảo history là danh sách
    if not isinstance(license.history, list):
        license.history = []

    # Thêm mục mới vào history
    new_history_entry = {
        "action": "Đổi Key",
        "date": gmt7_time.strftime('%H:%M %d-%m-%Y'),
        "details": "Admin thay đổi API Key"
    }
    license.history.append(new_history_entry)
    flag_modified(license, "history")

    # Lưu thay đổi vào cơ sở dữ liệu
    db.session.commit()

    return jsonify({"message": "License key updated successfully", "new_key": new_key}), 200



@admin_bp.route('/licenses/<int:license_id>/change-status', methods=['POST'])
def change_status(license_id):
    license = License.query.get(license_id)

    if license.status == 'Active':
        license.status = 'InActive'
    else:
        license.status = 'Active'

    # Commit the change to the database
    db.session.commit()

    return jsonify({
        "message": "License status changed successfully",
        "license_id": license.id,
        "new_status": license.status
    }), 200

@admin_bp.route('/licenses/<int:license_id>/delete-key', methods=['POST'])
def delete_key(license_id):
    # Tìm license trong cơ sở dữ liệu
    license = License.query.get(license_id)

    # Xóa license khỏi cơ sở dữ liệu
    db.session.delete(license)
    db.session.commit()

    # Trả về phản hồi thành công
    return jsonify({
        "message": "License deleted successfully",
        "license_id": license_id
    }), 200

@admin_bp.route('/key-function/<int:license_id>', methods=['GET'])
def get_key_function(license_id):
    # Truy vấn License theo license_id
    license = License.query.get(license_id)
    if not license:
        return jsonify({"message": "License not found"}), 404
    
    # Truy vấn SubLicenseKey có function = "duty"
    sub_licenses = SubLicenseKey.query.filter_by(license_id=license.id, function="duty").all()
    
    if not sub_licenses:
        return jsonify({"message": "No Sub License found with 'duty' function"}), 404
    
    # Danh sách các duty function
    duty_functions = []
    
    for sub_license in sub_licenses:
        duty_function = DutyFunction.query.filter_by(sub_license_key_id=sub_license.id).first()
        if duty_function:
            duty_functions.append({
                "face_recognition": "on" if duty_function.face_recognition else "off",
                "heatmap": "on" if duty_function.heatmap else "off",
                "object_counting": "on" if duty_function.object_counting else "off",
                "license_plate": "on" if duty_function.license_plate else "off",
                "safe_danger_zone": "on" if duty_function.safe_danger_zone else "off"
            })


    print(duty_functions)
    return render_template('admin/duty_function.html', duty_functions=duty_functions, license_id=license_id)
    # Trả về danh sách các duty function vào HTML template



@admin_bp.route('/key-function/update_status/<int:license_id>', methods=['POST'])
def update_status(license_id):
    # Truy vấn License theo license_id
    license = License.query.get(license_id)
    if not license:
        print("License not found")
        return jsonify({"success": False, "message": "License not found"}), 404

    # Truy vấn SubLicenseKey có function = "duty"
    sub_licenses = SubLicenseKey.query.filter_by(license_id=license.id, function="duty").all()
    if not sub_licenses:
        print("No Sub License found with 'duty' function")
        return jsonify({"success": False, "message": "No Sub License found with 'duty' function"}), 404

    data = request.get_json()
    function_name = data.get('function')
    new_status = data.get('status')
    index = data.get('index')
    

    index = int(index) - 1  # Vì loop.index trong Jinja bắt đầu từ 1, nên trừ đi 1 để truy cập đúng
    if index < 0 or index >= len(sub_licenses):
        return jsonify({"success": False, "message": "Index out of range"}), 400

    # Lấy sub_license tương ứng và duty_function của nó
    sub_license = sub_licenses[index]
    duty_function = DutyFunction.query.filter_by(sub_license_key_id=sub_license.id).first()
    if not duty_function:
        print("Duty function not found")
        return jsonify({"success": False, "message": "Duty function not found"}), 404

    # Kiểm tra xem đối tượng duty_function có thuộc tính function_name không
    if hasattr(duty_function, function_name):
        setattr(duty_function, function_name, True if new_status == "on" else False)
        db.session.commit()
        return jsonify({"success": True, "message": f"Updated {function_name} to {new_status}"})
    else:
        print("Function not found")
        return jsonify({"success": False, "message": "Function not found"}), 404






    data = request.get_json()
    function_name = data.get('function')
    new_status = data.get('status')
    index = data.get('index')
    try:
        # Vì loop.index trong Jinja bắt đầu từ 1, nên trừ đi 1 để truy cập đúng phần tử
        index = int(index) - 1
        if function_name in duty_functions[index]:
            duty_functions[index][function_name] = new_status
            return jsonify({"success": True, "message": f"Updated {function_name} to {new_status}"})
        else:
            return jsonify({"success": False, "message": "Function not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


#########################################################################################
####### --------------------------- LogsHistory --------------------------- #############
#########################################################################################


@admin_bp.route('/logs')
def logs_list():
    page = request.args.get('page', 1, type=int)  # Lấy số trang từ request, mặc định là trang 1
    per_page = 50  # Số logs mỗi trang

    logs = LogsHistory.query.order_by(LogsHistory.time.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/logs.html', logs=logs)


#########################################################################################
####### --------------------------- Role of the user --------------------------- ########
#########################################################################################



@admin_bp.route('/roles', methods=['GET'])
def get_roles():
    if check_admin() == False:
        return redirect('/admin/login')
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

@admin_bp.route('/roles/add', methods=['GET', 'POST'])
def add_role():
    if check_admin() == False:
        return redirect('/admin/login')

    if request.method == 'POST':
        name = request.form.get('name')
        permissions = request.form.getlist('permissions')  # Lấy danh sách quyền

        if name:
            new_role = Role(name=name, permissions=permissions)
            db.session.add(new_role)
            db.session.commit()
            flash("Role đã được thêm thành công!", "success")
            return redirect('/admin/roles')

    available_permissions = current_app.config["AVAILABLE_PERMISSIONS"]
    return render_template('admin/add_role.html', available_permissions=available_permissions)

@admin_bp.route('/<int:userid>/edit-user', methods=['GET', 'POST'])
def edit_user(userid):
    if not check_admin():
        return redirect('/admin/login')
    
    user = Users.query.get_or_404(userid)
    roles = Role.query.all()
    
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        
        role_id = request.form.get('role')  # Lấy ID của role từ form
        role = Role.query.get(role_id)  # Lấy object Role từ database
        
        if role:
            user.role = role.name  # Lưu tên role vào user
        
        db.session.commit()
        flash('Thông tin người dùng đã được cập nhật!', 'success')
        return jsonify({"success": True, "message": "Thông tin người dùng đã được cập nhật."})
    
    return render_template('admin/edit_user.html', user=user, roles=roles)


@admin_bp.route('/<int:role_id>/edit-role', methods=['GET', 'POST'])
def edit_role(role_id):
    if not check_admin():
        return redirect('/admin/login')
    role = Role.query.get_or_404(role_id)
    available_permissions = current_app.config["AVAILABLE_PERMISSIONS"]
    if request.method == 'POST':
        role.name = request.form.get('name')
        role.permissions = request.form.getlist('permissions')  # Lấy danh sách quyền
        db.session.commit()
        flash("Role đã được cập nhật thành công!", "success")
        return redirect('/admin/roles')
    
    return render_template('admin/edit_role.html', role=role, available_permissions=available_permissions)

