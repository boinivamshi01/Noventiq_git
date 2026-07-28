import os
import sqlite3
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")
CART = {}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_url TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """
    )
    conn.commit()
    conn.close()


def seed_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) as count FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_products = [
            ("Wireless Headphones", "Noise-cancelling Bluetooth headphones.", 99.99, "https://via.placeholder.com/300x300?text=Headphones"),
            ("Smart Watch", "Fitness tracker with heart rate monitor.", 149.99, "https://via.placeholder.com/300x300?text=Smart+Watch"),
            ("Portable Speaker", "Waterproof speaker with rich bass.", 69.99, "https://via.placeholder.com/300x300?text=Speaker"),
            ("Laptop Backpack", "Durable backpack with laptop compartment.", 59.99, "https://via.placeholder.com/300x300?text=Backpack"),
            ("Wireless Mouse", "Ergonomic mouse with USB receiver.", 29.99, "https://via.placeholder.com/300x300?text=Mouse"),
        ]
        cursor.executemany(
            "INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)",
            sample_products,
        )
    conn.commit()
    conn.close()


def row_to_dict(row):
    return {key: row[key] for key in row.keys()}


@app.route("/api/products", methods=["GET"])
def list_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([row_to_dict(product) for product in products])


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        abort(404, description="Product not found")
    return jsonify(row_to_dict(product))


@app.route("/api/cart", methods=["GET"])
def get_cart():
    cart_items = []
    conn = get_db_connection()
    for product_id, quantity in CART.items():
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product:
            item = row_to_dict(product)
            item["quantity"] = quantity
            item["subtotal"] = round(item["price"] * quantity, 2)
            cart_items.append(item)
    conn.close()
    total = round(sum(item["subtotal"] for item in cart_items), 2)
    return jsonify({"items": cart_items, "total": total})


@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if not product_id or quantity <= 0:
        abort(400, description="Invalid product ID or quantity")
    conn = get_db_connection()
    product = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        abort(404, description="Product not found")
    CART[product_id] = CART.get(product_id, 0) + quantity
    return jsonify({"message": "Product added to cart", "cart": CART}), 201


@app.route("/api/cart/<int:product_id>", methods=["PUT"])
def update_cart_item(product_id):
    data = request.get_json() or {}
    quantity = data.get("quantity")
    if quantity is None or quantity < 0:
        abort(400, description="Invalid quantity")
    if product_id not in CART:
        abort(404, description="Product not in cart")
    if quantity == 0:
        del CART[product_id]
    else:
        CART[product_id] = quantity
    return jsonify({"message": "Cart updated", "cart": CART})


@app.route("/api/cart/<int:product_id>", methods=["DELETE"])
def remove_cart_item(product_id):
    if product_id not in CART:
        abort(404, description="Product not in cart")
    del CART[product_id]
    return jsonify({"message": "Item removed from cart", "cart": CART})


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    name = data.get("customer_name")
    email = data.get("customer_email")
    if not name or not email:
        abort(400, description="Customer name and email are required")
    if not CART:
        abort(400, description="Cart is empty")

    conn = get_db_connection()
    cursor = conn.cursor()
    cart_items = []
    total = 0.0
    for product_id, quantity in CART.items():
        product = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            continue
        price = product["price"]
        subtotal = price * quantity
        total += subtotal
        cart_items.append((product_id, quantity, price))

    if not cart_items:
        conn.close()
        abort(400, description="No valid items in cart")

    cursor.execute(
        "INSERT INTO orders (customer_name, customer_email, total) VALUES (?, ?, ?)",
        (name, email, round(total, 2)),
    )
    order_id = cursor.lastrowid
    for product_id, quantity, price in cart_items:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
            (order_id, product_id, quantity, price),
        )
    conn.commit()
    conn.close()
    CART.clear()
    return jsonify({"message": "Order placed successfully", "order_id": order_id, "total": round(total, 2)})


@app.route("/api/orders", methods=["GET"])
def list_orders():
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    results = []
    for order in orders:
        items = conn.execute(
            "SELECT oi.product_id, oi.quantity, oi.price, p.name, p.image_url FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?",
            (order["id"],),
        ).fetchall()
        results.append(
            {
                "id": order["id"],
                "customer_name": order["customer_name"],
                "customer_email": order["customer_email"],
                "total": order["total"],
                "created_at": order["created_at"],
                "items": [
                    {
                        "product_id": item["product_id"],
                        "name": item["name"],
                        "quantity": item["quantity"],
                        "price": item["price"],
                        "image_url": item["image_url"],
                    }
                    for item in items
                ],
            }
        )
    conn.close()
    return jsonify(results)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404


if __name__ == "__main__":
    init_db()
    seed_products()
    app.run(host="0.0.0.0", port=5000, debug=True)
