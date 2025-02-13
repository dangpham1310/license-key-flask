from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from routes.authentication import auth_bp
from routes.license import license_bp
from routes.admin import admin_bp
from models import db
from config import Config
from flask_migrate import Migrate
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo SQLAlchemy
db.init_app(app)

migrate = Migrate(app, db)

# Khởi tạo JWTManager
jwt = JWTManager(app)

# Đăng ký Blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(license_bp, url_prefix='/license')
app.register_blueprint(admin_bp, url_prefix='/admin')



if __name__ == '__main__':
    # Tạo database khi chạy ứng dụng
    with app.app_context():
        db.create_all()
    app.run(debug=True, port = 8080,host = "0.0.0.0")
