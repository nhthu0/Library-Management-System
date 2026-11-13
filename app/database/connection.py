
import mysql.connector
from app.config.settings import DB_CONFIG


def get_connection():
    """Tạo kết nối tới MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def test_connection():
    """Kiểm tra kết nối và database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]

        print(f"Connected to database: {database_name}")

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"Total tables: {len(tables)}")

        for table in tables:
            print(f"- {table[0]}")

        cursor.close()
        conn.close()
        return True

    except mysql.connector.Error as error:
        print(f"Database connection failed: {error}")
        return False


if __name__ == "__main__":
    test_connection()
