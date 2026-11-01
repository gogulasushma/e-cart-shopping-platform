
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash
import uuid


app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-your-project"


# ---------------- SHARED STORAGE ----------------

ORDERS = []
USERS = {}
WISHLISTS = {}

ORDER_STATUSES = [
    "Pending",
    "Processing",
    "Shipped",
    "Delivered",
    "Cancelled"
]


# ---------------- PRODUCT DATA ----------------

PRODUCTS = {
    1: {"name": "Women's Kurti", "category": "Clothing", "price": 499, "stock": 20, "image": "https://images.unsplash.com/photo-1583391733956-6c78276477e3?auto=format&fit=crop&w=700&q=80"},
    2: {"name": "Cotton Saree", "category": "Clothing", "price": 799, "stock": 15, "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=700&q=80"},
    3: {"name": "Men's T-Shirt", "category": "Clothing", "price": 349, "stock": 25, "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=700&q=80"},
    4: {"name": "Jeans", "category": "Clothing", "price": 699, "stock": 18, "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=700&q=80"},
    5: {"name": "Handbag", "category": "Accessories", "price": 599, "stock": 12, "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=700&q=80"},
    6: {"name": "Women's Sandals", "category": "Footwear", "price": 399, "stock": 20, "image": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=700&q=80"},
    7: {"name": "Men's Shoes", "category": "Footwear", "price": 999, "stock": 10, "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80"},
    8: {"name": "Wall Clock", "category": "Home", "price": 299, "stock": 15, "image": "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?auto=format&fit=crop&w=700&q=80"},
    9: {"name": "Water Bottle", "category": "Home", "price": 199, "stock": 30, "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=700&q=80"},
    10: {"name": "Bedsheet", "category": "Home", "price": 499, "stock": 20, "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=700&q=80"},
    11: {"name": "Face Wash", "category": "Beauty", "price": 249, "stock": 25, "image": "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=700&q=80"},
    12: {"name": "Lipstick", "category": "Beauty", "price": 199, "stock": 20, "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=700&q=80"},
    13: {"name": "Bluetooth Speaker", "category": "Electronics", "price": 1299, "stock": 10, "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=700&q=80"},
    14: {"name": "Headphones", "category": "Electronics", "price": 799, "stock": 15, "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=700&q=80"},
    15: {"name": "Kitchen Storage Box", "category": "Home", "price": 249, "stock": 25, "image": "https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=700&q=80"}
}


CATEGORIES = [
    "Clothing",
    "Accessories",
    "Footwear",
    "Home",
    "Beauty",
    "Electronics"
]


# ---------------- COMMON FUNCTIONS ----------------

def cart_data():

    cart = session.get("cart", {})
    items = []
    subtotal = 0

    for pid_text, quantity in cart.items():

        pid = int(pid_text)
        product = PRODUCTS.get(pid)

        if not product:
            continue

        quantity = int(quantity)
        amount = product["price"] * quantity
        subtotal += amount

        items.append({
            "id": pid,
            **product,
            "quantity": quantity,
            "amount": amount
        })

    return items, subtotal


def discount_for(subtotal):

    if subtotal >= 5000:
        return 15
    if subtotal >= 2000:
        return 10
    if subtotal >= 1000:
        return 5

    return 0


def validate_product_details(name, category, price, stock, image):

    if len(name) < 2 or len(name) > 100:
        return "Product name must contain 2 to 100 characters."

    if category not in CATEGORIES:
        return "Please select a valid product category."

    if price < 1 or price > 1000000:
        return "Price must be between 1 and 10,00,000."

    if stock < 0 or stock > 100000:
        return "Stock must be between 0 and 1,00,000."

    if len(image) > 2000:
        return "Image URL is too long."

    parsed_url = urlparse(image)

    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        return "Please enter a valid image URL."

    return None


@app.context_processor
def common_values():

    cart = session.get("cart", {})
    customer_id = session.get("customer_id")

    wishlist = WISHLISTS.get(customer_id, []) if customer_id else []

    return {
        "cart_count": sum(int(q) for q in cart.values()),
        "wishlist_count": len(wishlist),
        "categories": CATEGORIES
    }


# ---------------- CUSTOMER REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")

        elif email in USERS:
            flash("This email is already registered.", "error")

        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")

        elif password != confirm_password:
            flash("Passwords do not match.", "error")

        else:

            customer_id = str(uuid.uuid4())

            USERS[email] = {
                "customer_id": customer_id,
                "name": name,
                "email": email,
                "password": generate_password_hash(password)
            }

            WISHLISTS[customer_id] = []

            flash("Registration successful! Please log in.", "success")

            return redirect(url_for("customer_login"))

    return render_template("register.html")


# ---------------- CUSTOMER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def customer_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        customer = USERS.get(email)

        if customer and check_password_hash(customer["password"], password):

            session["customer_id"] = customer["customer_id"]
            session["customer_name"] = customer["name"]
            session["customer_email"] = customer["email"]

            WISHLISTS.setdefault(customer["customer_id"], [])

            flash("Welcome back, " + customer["name"] + "!", "success")

            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------- CUSTOMER LOGOUT ----------------

@app.route("/logout")
def customer_logout():

    session.pop("customer_id", None)
    session.pop("customer_name", None)
    session.pop("customer_email", None)

    flash("You have logged out successfully.", "success")

    return redirect(url_for("home"))


# ---------------- CUSTOMER WEBSITE ----------------

@app.route("/")
def home():

    featured = list(PRODUCTS.items())[:8]

    return render_template("index.html", featured=featured)


@app.route("/products")
def products():

    keyword = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()

    results = []

    for pid, product in PRODUCTS.items():

        if category and product["category"].lower() != category.lower():
            continue

        if keyword and (
            keyword not in product["name"].lower()
            and keyword not in product["category"].lower()
        ):
            continue

        results.append((pid, product))

    return render_template(
        "products.html",
        products=results,
        query=request.args.get("q", ""),
        selected_category=category
    )


# ---------------- ADD TO CART ----------------

@app.route("/add-to-cart/<int:pid>", methods=["POST"])
def add_to_cart(pid):

    if pid not in PRODUCTS:
        flash("That product could not be found.", "error")
        return redirect(url_for("products"))

    try:
        quantity = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 0

    cart = session.get("cart", {})
    current = int(cart.get(str(pid), 0))
    available = PRODUCTS[pid]["stock"] - current

    if quantity < 1:

        flash("Please choose a quantity greater than zero.", "error")

    elif quantity > available:

        flash(
            f"Only {max(available, 0)} more item(s) can be added.",
            "error"
        )

    else:

        cart[str(pid)] = current + quantity
        session["cart"] = cart

        flash(f"{PRODUCTS[pid]['name']} added to your cart!", "success")

    return redirect(request.referrer or url_for("products"))


# ---------------- CUSTOMER WISHLIST ----------------

@app.route("/wishlist")
def wishlist():

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please log in to view your wishlist.", "error")
        return redirect(url_for("customer_login"))

    saved_ids = WISHLISTS.setdefault(customer_id, [])

    wishlist_items = []

    for pid in saved_ids:

        product = PRODUCTS.get(pid)

        if product:
            wishlist_items.append((pid, product))

    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )


# ---------------- ADD TO WISHLIST ----------------

@app.route("/wishlist/add/<int:pid>", methods=["POST"])
def add_to_wishlist(pid):

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please log in to save products to your wishlist.", "error")
        return redirect(url_for("customer_login"))

    if pid not in PRODUCTS:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    saved_ids = WISHLISTS.setdefault(customer_id, [])

    if pid in saved_ids:
        flash("This product is already in your wishlist.", "error")

    else:
        saved_ids.append(pid)
        flash("Product added to your wishlist!", "success")

    return redirect(request.referrer or url_for("wishlist"))


# ---------------- REMOVE FROM WISHLIST ----------------

@app.route("/wishlist/remove/<int:pid>", methods=["POST"])
def remove_from_wishlist(pid):

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please log in to manage your wishlist.", "error")
        return redirect(url_for("customer_login"))

    saved_ids = WISHLISTS.setdefault(customer_id, [])

    if pid in saved_ids:
        saved_ids.remove(pid)
        flash("Product removed from your wishlist.", "success")

    else:
        flash("Product was not found in your wishlist.", "error")

    return redirect(url_for("wishlist"))


# ---------------- CART ----------------

@app.route("/cart")
def cart():

    items, subtotal = cart_data()

    rate = discount_for(subtotal)
    discount = subtotal * rate // 100

    return render_template(
        "cart.html",
        items=items,
        subtotal=subtotal,
        rate=rate,
        discount=discount,
        total=subtotal - discount
    )


# ---------------- UPDATE CART ----------------

@app.route("/update-cart/<int:pid>", methods=["POST"])
def update_cart(pid):

    cart = session.get("cart", {})

    if str(pid) not in cart or pid not in PRODUCTS:
        flash("That item is not in your cart.", "error")
        return redirect(url_for("cart"))

    try:
        quantity = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 0

    if quantity <= 0:

        cart.pop(str(pid), None)
        flash("Item removed from your cart.", "success")

    elif quantity > PRODUCTS[pid]["stock"]:

        flash(
            f"Only {PRODUCTS[pid]['stock']} item(s) are available.",
            "error"
        )

    else:

        cart[str(pid)] = quantity
        flash("Cart updated successfully.", "success")

    session["cart"] = cart

    return redirect(url_for("cart"))


# ---------------- REMOVE FROM CART ----------------

@app.route("/remove-from-cart/<int:pid>", methods=["POST"])
def remove_from_cart(pid):

    cart = session.get("cart", {})

    cart.pop(str(pid), None)
    session["cart"] = cart

    flash("Product removed from your cart.", "success")

    return redirect(url_for("cart"))


# ---------------- CHECKOUT ----------------

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if not session.get("customer_id"):
        flash("Please log in before placing your order.", "error")
        return redirect(url_for("customer_login"))

    items, subtotal = cart_data()

    if not items:
        flash("Your cart is empty. Add products before checkout.", "error")
        return redirect(url_for("products"))

    rate = discount_for(subtotal)
    discount = subtotal * rate // 100
    total = subtotal - discount

    if request.method == "POST":

        for item in items:

            if item["quantity"] > PRODUCTS[item["id"]]["stock"]:

                flash(
                    f"Not enough stock for {item['name']}. Please update your cart.",
                    "error"
                )

                return redirect(url_for("cart"))

        order_no = max(
            [order["order_number"] for order in ORDERS],
            default=1000
        ) + 1

        order = {
            "order_number": order_no,
            "customer_id": session["customer_id"],
            "items": [
                {
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "amount": item["amount"]
                }
                for item in items
            ],
            "subtotal": subtotal,
            "discount_rate": rate,
            "discount": discount,
            "total": total,
            "status": "Pending",
            "date": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }

        for item in items:
            PRODUCTS[item["id"]]["stock"] -= item["quantity"]

        ORDERS.append(order)

        session["cart"] = {}
        session["latest_order"] = order

        return redirect(url_for("order_success"))

    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        rate=rate,
        discount=discount,
        total=total
    )


# ---------------- ORDER SUCCESS ----------------

@app.route("/order-success")
def order_success():

    order = session.get("latest_order")

    if not order:
        return redirect(url_for("home"))

    return render_template("order_success.html", order=order)


# ---------------- CUSTOMER PURCHASE HISTORY ----------------

@app.route("/orders")
def orders():

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please log in to view your orders.", "error")
        return redirect(url_for("customer_login"))

    customer_orders = [
        order for order in ORDERS
        if order["customer_id"] == customer_id
    ]

    return render_template(
        "purchase_history.html",
        orders=list(reversed(customer_orders))
    )


# ---------------- CUSTOMER ORDER CANCELLATION ----------------

@app.route("/orders/cancel/<int:order_number>", methods=["POST"])
def cancel_order(order_number):

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please log in to cancel your order.", "error")
        return redirect(url_for("customer_login"))

    for order in ORDERS:

        if (
            order["order_number"] == order_number
            and order["customer_id"] == customer_id
        ):

            if order["status"] not in ["Pending", "Processing"]:

                flash(
                    "This order cannot be cancelled now.",
                    "error"
                )

                return redirect(url_for("orders"))

            order["status"] = "Cancelled"

            flash(
                f"Order #{order_number} cancelled successfully!",
                "success"
            )

            return redirect(url_for("orders"))

    flash("Order not found.", "error")

    return redirect(url_for("orders"))


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "Admin@123":

            session["is_admin"] = True

            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    return render_template(
        "admin/dashboard.html",
        total_products=len(PRODUCTS),
        total_stock=sum(p["stock"] for p in PRODUCTS.values()),
        total_orders=len(ORDERS),
        total_sales=sum(order["total"] for order in ORDERS)
    )


# ---------------- ADMIN LOGOUT ----------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("is_admin", None)

    flash("You have logged out successfully.", "success")

    return redirect(url_for("admin_login"))


# ---------------- ADMIN ORDER MANAGEMENT ----------------

@app.route("/admin/orders")
def admin_orders():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    return render_template(
        "admin/orders.html",
        orders=list(reversed(ORDERS)),
        order_statuses=ORDER_STATUSES
    )


@app.route("/admin/orders/update/<int:order_number>", methods=["POST"])
def update_order_status(order_number):

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    new_status = request.form.get("status", "").strip()

    if new_status not in ORDER_STATUSES:
        flash("Invalid order status.", "error")
        return redirect(url_for("admin_orders"))

    for order in ORDERS:

        if order["order_number"] == order_number:

            order["status"] = new_status

            flash("Order status updated successfully!", "success")

            break

    else:

        flash("Order not found.", "error")

    return redirect(url_for("admin_orders"))


# ---------------- ADMIN PRODUCT MANAGEMENT ----------------

@app.route("/admin/products")
def admin_products():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    keyword = request.args.get("search", "").strip().lower()
    keyword = keyword.replace(" ", "")

    selected_category = request.args.get("category", "").strip()

    filtered_products = []

    for pid, product in PRODUCTS.items():

        product_name = product["name"].lower().replace(" ", "")
        product_category = product["category"].lower().replace(" ", "")

        if keyword and (
            keyword not in product_name
            and keyword not in product_category
        ):
            continue

        if selected_category and product["category"] != selected_category:
            continue

        filtered_products.append((pid, product))

    return render_template(
        "admin/products.html",
        products=filtered_products,
        categories=CATEGORIES
    )


# ---------------- ADD PRODUCT ----------------

@app.route("/admin/products/add", methods=["GET", "POST"])
def add_product():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        image = request.form.get("image", "").strip()

        try:
            price = int(request.form.get("price", ""))
            stock = int(request.form.get("stock", ""))

        except (ValueError, TypeError):

            flash("Price and stock must be valid whole numbers.", "error")

            return redirect(url_for("add_product"))

        error = validate_product_details(
            name, category, price, stock, image
        )

        if error:

            flash(error, "error")

            return redirect(url_for("add_product"))

        new_id = max(PRODUCTS.keys(), default=0) + 1

        PRODUCTS[new_id] = {
            "name": name,
            "category": category,
            "price": price,
            "stock": stock,
            "image": image
        }

        flash("Product added successfully!", "success")

        return redirect(url_for("admin_products"))

    return render_template(
        "admin/add_product.html",
        categories=CATEGORIES
    )


# ---------------- EDIT PRODUCT ----------------

@app.route("/admin/products/edit/<int:pid>", methods=["GET", "POST"])
def edit_product(pid):

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    product = PRODUCTS.get(pid)

    if product is None:

        flash("Product not found!", "error")

        return redirect(url_for("admin_products"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        image = request.form.get("image", "").strip()

        try:
            price = int(request.form.get("price", ""))
            stock = int(request.form.get("stock", ""))

        except (ValueError, TypeError):

            flash("Price and stock must be valid whole numbers.", "error")

            return redirect(url_for("edit_product", pid=pid))

        error = validate_product_details(
            name, category, price, stock, image
        )

        if error:

            flash(error, "error")

            return redirect(url_for("edit_product", pid=pid))

        product["name"] = name
        product["category"] = category
        product["price"] = price
        product["stock"] = stock
        product["image"] = image

        flash("Product updated successfully!", "success")

        return redirect(url_for("admin_products"))

    return render_template(
        "admin/edit_product.html",
        product=product,
        categories=CATEGORIES
    )


# ---------------- DELETE PRODUCT ----------------

@app.route("/admin/products/delete/<int:pid>", methods=["POST"])
def delete_product(pid):

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if pid not in PRODUCTS:

        flash("Product not found!", "error")

        return redirect(url_for("admin_products"))

    del PRODUCTS[pid]

    # Remove deleted product from all customer wishlists
    for customer_wishlist in WISHLISTS.values():
        if pid in customer_wishlist:
            customer_wishlist.remove(pid)

    flash("Product deleted successfully!", "success")

    return redirect(url_for("admin_products"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
