import sqlite3

database = 'test_database.db'

create_user_table = """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    password TEXT NOT NULL
);
"""

test_users = [
    (1, "Emil", "password123"),
    (2, "Frieda", "password234"),
    (3, "Oskar", "password345"),
]

try:
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute(create_user_table)
        cursor.executemany(
            """
            INSERT OR IGNORE INTO users (id, name, password)
            VALUES (?, ?, ?)
            """,
            test_users
        )
        conn.commit()
        
        print("Database successfully initialized and successfully inserted test_users.")
        
except sqlite3.OperationalError as error:
    print(f"Database could not be created due to an error: {error}.")