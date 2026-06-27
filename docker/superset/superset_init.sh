#!/bin/bash
set -e

# Install PostgreSQL driver to virtualenv site-packages
pip install --target=/app/.venv/lib/python3.10/site-packages psycopg2-binary

# Initialize superset database
superset db upgrade

# Create admin user
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@adventureworks.com \
    --password admin

# Initialize default roles and permissions
superset init

# Automatically connect PostgreSQL database
echo "=== Automatically Connecting to PostgreSQL DWH ==="
python3 - << 'EOF'
try:
    from superset.app import create_app
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.models.core import Database
        existing = db.session.query(Database).filter_by(database_name="AdventureWorks DWH").first()
        if not existing:
            d = Database(
                database_name="AdventureWorks DWH",
                sqlalchemy_uri="postgresql://postgres:postgres@postgres_dwh:5432/adventureworks_dwh"
            )
            db.session.add(d)
            db.session.commit()
            print("SUCCESS: Database connection created.")
        else:
            print("SUCCESS: Database connection already exists.")
except Exception as e:
    print(f"ERROR: {e}")
EOF

# Keep container running or start the server
exec /usr/bin/run-server.sh
