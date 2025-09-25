from app import app, db, Admin
from werkzeug.security import generate_password_hash

# Use the application context
with app.app_context():
    # Create all tables if they don't exist
    db.create_all()

    # Check if admin exists
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin")
        admin.password_hash = generate_password_hash("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully!")
    else:
        print("Admin already exists.")
