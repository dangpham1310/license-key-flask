class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://remote_user:wySkX74EUHhmtW2BvrJ5bC63uVPGdsjecNLDYxTafQn8zAZMKF@127.0.0.1:5051/license-key-manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'Jzn3f5cxaqVYR6bmuyBZ9h4gAFrjLQPUwHM7XTNKskvedWtSCp'
    JWT_SECRET_KEY = 'xDs8CQZNuMXb2PvkyqLYra9T3EAUmzwBdfh7n4KtFS6eRjWGcg'  # Thêm khóa bí mật cho JWT
    AVAILABLE_PERMISSIONS = ["Dashboard", "Users", "Vai Trò"]
        # Dành cho lúc dev:
        # chạy cái này trước
        # Start-Process -FilePath "cloudflared.exe" -ArgumentList "access tcp --hostname mysql.dannycode.site --url localhost:5051" -WindowStyle Hidden
        # Chạy xong sẽ liên kết với server thông qua tunnel của cloudflare => có thể connect từ xa và dùng ip là 127.0.0.1:5051
        # Stop-Process -Name "cloudflared"