#!/bin/bash
# Initialize or migrate database on deployment

cd /var/app/current

# Check if database exists
if [ -f "database.db" ]; then
    echo "Database exists - running migrations to update schema..."
    # SQLAlchemy's create_all() will add new tables/columns without dropping existing ones
    /var/app/venv/*/bin/python init_db.py
    echo "Database schema updated (existing data preserved)"
else
    echo "Database does not exist - creating and seeding..."
    # Initialize database
    /var/app/venv/*/bin/python init_db.py
    # Seed with initial data
    /var/app/venv/*/bin/python seed_data.py
    echo "Database created and seeded!"
fi
