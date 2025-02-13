class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://remote_user:wySkX74EUHhmtW2BvrJ5bC63uVPGdsjecNLDYxTafQn8zAZMKF@127.0.0.1:5051/license-key-manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'Jzn3f5cxaqVYR6bmuyBZ9h4gAFrjLQPUwHM7XTNKskvedWtSCp'
    JWT_SECRET_KEY = 'xDs8CQZNuMXb2PvkyqLYra9T3EAUmzwBdfh7n4KtFS6eRjWGcg'  # Thêm khóa bí mật cho JWT
    AVAILABLE_PERMISSIONS = ["Dashboard", "Users", "Vai Trò"]
