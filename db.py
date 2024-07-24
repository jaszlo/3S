import duckdb
import sys

DB_PATH = "images.duckdb"

class Database:
    def __init__(self):
        with duckdb.connect(database=DB_PATH) as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id VARCHAR PRIMARY KEY,
                filename VARCHAR,
                data BLOB
            )
            """)

    def insert_image(self, filename, file_data):
        file_id = (hash(file_data)  % (sys.maxsize + 1) * 2) # To prevent negative hashes
        with duckdb.connect(database=DB_PATH) as con:
            # Check if file exist and then return
            if con.execute("SELECT * FROM images WHERE id = ?", (file_id,)).fetchone():
                return file_id
            con.execute(
                "INSERT INTO images (id, filename, data) VALUES (?, ?, ?)",
                (file_id, filename, file_data)
            )
            return file_id

    def get_image(self, file_id):
        with duckdb.connect(database=DB_PATH) as con:
            result = con.execute(
                "SELECT filename, data FROM images WHERE id = ?",
                (file_id,)
            ).fetchone()

            return (result, result is not None)
    
    def get_images(self):
        with duckdb.connect(database=DB_PATH) as con:
            return con.execute("SELECT id, filename, OCTET_LENGTH(data) FROM images").fetchall()

    def clear(self):
        with duckdb.connect(database=DB_PATH) as con:
            return con.execute("DELETE FROM images").rowcount
