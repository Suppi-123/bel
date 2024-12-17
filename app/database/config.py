from pony.orm import Database
from dotenv import load_dotenv
import os

# Initialize dotenv for environment variables
load_dotenv()

# Create the database connection
db = Database()

# Bind the database with the connection details from the environment variables
db.bind(
    provider='postgres',  # You can use another provider like 'sqlite', 'mysql', etc.
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME')
)

def initialize_database():
    """
    Initialize the database schema and create necessary tables if they do not exist.
    """
    if not hasattr(db, 'mapping_generated') or not db.mapping_generated:
        # Generate mapping and create tables if they don't exist
        db.generate_mapping(create_tables=True)  # Will create the tables if they don't exist
        db.mapping_generated = True
    else:
        # Optionally, you can reset the mapping if you are making changes
        db.mapping_generated = False  # Reset the flag to allow re-generation
        db.generate_mapping(create_tables=True)  # Re-generate mapping