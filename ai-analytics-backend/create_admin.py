import bcrypt
from app.database import SessionLocal
from app.models import User

db = SessionLocal()

password = "my_secret_password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

new_user = User(email="admin@example.com", password_hash=hashed)
db.add(new_user)
db.commit()
print("Пользователь успешно создан с правильным хэшем!")