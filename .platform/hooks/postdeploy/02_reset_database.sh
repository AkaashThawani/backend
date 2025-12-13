#!/bin/bash
# Initialize or migrate database on deployment

cd /var/app/current

# Ensure the current directory is writable
chmod 755 /var/app/current

# Check if database exists
if [ -f "reddit_mastermind.db" ]; then
    echo "Database exists - running migrations to update schema..."
    # Set correct permissions on existing database
    chmod 666 reddit_mastermind.db
    # SQLAlchemy's create_all() will add new tables/columns without dropping existing ones
    /var/app/venv/*/bin/python init_db.py
    # Ensure permissions are still correct after migration
    chmod 666 reddit_mastermind.db
    echo "Database schema updated (existing data preserved)"
else
    echo "Database does not exist - creating and seeding..."
    # Initialize database
    /var/app/venv/*/bin/python init_db.py
    # Set correct permissions on new database
    chmod 666 reddit_mastermind.db
    # Seed with initial data
    /var/app/venv/*/bin/python seed_data.py
    echo "Database created and seeded!"
fi

# Final permission check
if [ -f "reddit_mastermind.db" ]; then
    chmod 666 reddit_mastermind.db
    echo "Database permissions set to 666 (read/write for all)"
fi
