from main import SessionLocal, User, pwd_context

db = SessionLocal()

admin = User(
    email='admin@test.com',
    hashed_password=pwd_context.hash('admin123'),
    full_name='Administrator',
    is_admin=True
)

db.add(admin)
db.commit()

print('Admin created successfully!')
print('Email: admin@test.com')
print('Password: admin123')

db.close()
