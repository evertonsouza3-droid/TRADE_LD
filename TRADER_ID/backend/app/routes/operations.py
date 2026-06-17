from app.database import get_connection


def create_operation(payload):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO operations (name, symbol, quantity, price) VALUES (?, ?, ?, ?)",
            (
                payload["name"],
                payload["symbol"],
                payload["quantity"],
                payload["price"],
            ),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "name": payload["name"],
            "symbol": payload["symbol"],
            "quantity": payload["quantity"],
            "price": payload["price"],
        }
    finally:
        conn.close()


def list_operations():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, symbol, quantity, price FROM operations ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
