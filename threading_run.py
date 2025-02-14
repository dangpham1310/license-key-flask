import threading
import time
from datetime import datetime
from models import db, License
from flask import Flask

def check_license_expiry(app):
    while True:
        with app.app_context():  # Cần dùng app context để truy cập database
            current_time = datetime.now()
            print(f"\n🔍 Checking license expiry at {current_time}\n")
            # Chỉ lấy license chưa hết hạn và có ngày hết hạn trước hiện tại
            expired_licenses = License.query.filter(
                License.expiry_date < current_time,  # License đã quá hạn
                License.status != "Expired"  # Chưa được đánh dấu "Expired"
            ).all()

            if not expired_licenses:
                print("✅ No expired licenses found. Waiting 60s...\n")
            else:
                for license in expired_licenses:
                    print(f"   ❌ License {license.license_key} is now EXPIRED!")
                    license.status = "Expired"

                db.session.commit()  # Cập nhật tất cả license trong một lần commit


        time.sleep(60)  # Chạy lại sau 60 giây

def start_expiry_thread(app):
    thread = threading.Thread(target=check_license_expiry, args=(app,), daemon=True)
    thread.start()
    print("✅ Quy Trình Chạy Kiểm Tra Hết Hạn Bắt Đầu!")
