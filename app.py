from flask import Flask, jsonify, request, render_template_string
from models import Product, Cart, Order

app = Flask(__name__)

# Инициализация данных
products = [
    Product(1, "Ноутбук Dell XPS", 150000, "электроника", 10),
    Product(2, "Книга 'Python для начинающих'", 1500, "книги", 25),
    Product(3, "Кофеварка", 7500, "бытовая техника", 5),
    Product(4, "Футболка Python", 1200, "одежда", 50),
    Product(5, "Наушники Sony", 8500, "электроника", 15)
]

cart = Cart()
orders = []

# HTML шаблоны
HOME_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Магазин</title>
</head>
<body>
    <h1>🛒 Онлайн магазин</h1>
    <p>Добро пожаловать в наш магазин!</p>
    <ul>
        <li><a href="/api/products">Все товары (API)</a></li>
        <li><a href="/cart">Корзина</a></li>
        <li><a href="/orders">Заказы</a></li>
        <li><a href="/stats">Статистика</a></li>
    </ul>
</body>
</html>
'''

CART_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Корзина</title>
</head>
<body>
    <h1>🛒 Ваша корзина</h1>
    {% if items %}
        <ul>
        {% for item in items %}
            <li>{{ item.name }} - {{ item.price }} руб. (x{{ item.quantity }})</li>
        {% endfor %}
        </ul>
        <p><strong>Итого: {{ total }} руб.</strong></p>
        <form action="/api/checkout" method="POST">
            <button type="submit">Оформить заказ</button>
        </form>
    {% else %}
        <p>Корзина пуста</p>
    {% endif %}
    <a href="/">На главную</a>
</body>
</html>
'''


@app.route('/')
def home():
    """Главная страница"""
    return render_template_string(HOME_HTML)


@app.route('/api/products', methods=['GET'])
def get_products():
    """Получить все товары"""
    return jsonify([p.to_dict() for p in products])


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Получить товар по ID"""
    product = next((p for p in products if p.id == product_id), None)
    if product:
        return jsonify(product.to_dict())
    return jsonify({'error': 'Товар не найден'}), 404


@app.route('/api/products', methods=['POST'])
def add_product():
    """Добавить новый товар (для администратора)"""
    data = request.get_json()

    if not data or 'name' not in data or 'price' not in data:
        return jsonify({'error': 'Необходимы name и price'}), 400

    new_id = max(p.id for p in products) + 1 if products else 1
    name = data['name']
    price = data['price']
    category = data.get('category', 'другое')
    stock = data.get('stock', 0)

    new_product = Product(new_id, name, price, category, stock)
    products.append(new_product)

    return jsonify({'message': 'Товар добавлен', 'product': new_product.to_dict()}), 201


@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Получить содержимое корзины"""
    return jsonify(cart.to_dict())


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Добавить товар в корзину"""
    data = request.get_json()

    if not data or 'product_id' not in data:
        return jsonify({'error': 'Необходим product_id'}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)

    product = next((p for p in products if p.id == product_id), None)
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Недостаточно товара на складе'}), 400

    # Добавляем в корзину
    cart.add_item(product, quantity)

    return jsonify({'message': 'Товар добавлен в корзину', 'cart': cart.to_dict()})


@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Удалить товар из корзины"""
    data = request.get_json()

    if not data or 'product_id' not in data:
        return jsonify({'error': 'Необходим product_id'}), 400

    product_id = data['product_id']

    product = next((p for p in products if p.id == product_id), None)
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404

    cart.remove_item(product_id)

    return jsonify({'message': 'Товар удален из корзины', 'cart': cart.to_dict()})


@app.route('/api/checkout', methods=['POST'])
def checkout():
    """Оформить заказ"""
    if not cart.items:
        return jsonify({'error': 'Корзина пуста'}), 400

    # Создаем заказ
    order = Order(len(orders) + 1, cart.items.copy(), cart.get_total())

    # Обновляем запасы
    for item in cart.items:
        product = next(p for p in products if p.id == item['product_id'])
        product.stock -= item['quantity']

    # Добавляем заказ в список
    orders.append(order)

    # Очищаем корзину
    cart.clear()

    return jsonify({'message': 'Заказ оформлен', 'order': order.to_dict()})


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получить все заказы"""
    return jsonify([order.to_dict() for order in orders])


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получить статистику магазина"""
    total_products = len(products)
    total_orders = len(orders)
    total_revenue = sum(order.total for order in orders)
    total_items_sold = sum(sum(item['quantity'] for item in order.items) for order in orders)

    # Самые популярные категории
    category_sales = {}
    for order in orders:
        for item in order.items:
            product = next(p for p in products if p.id == item['product_id'])
            category_sales[product.category] = category_sales.get(product.category, 0) + item['quantity']

    most_popular_category = max(category_sales.items(), key=lambda x: x[1])[0] if category_sales else 'нет продаж'

    return jsonify({
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'most_popular_category': most_popular_category,
        'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0
    })


@app.route('/cart')
def cart_page():
    """HTML страница корзины"""
    cart_data = cart.to_dict()
    return render_template_string(CART_HTML,
                                  items=cart_data['items'],
                                  total=cart_data['total'])


@app.route('/orders')
def orders_page():
    """HTML страница заказов"""
    orders_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Заказы</title>
    </head>
    <body>
        <h1>📋 Ваши заказы</h1>
        {% if orders %}
            <ul>
            {% for order in orders %}
                <li>
                    <strong>Заказ #{{ order.id }}</strong><br>
                    Сумма: {{ order.total }} руб.<br>
                    Товаров: {{ order.items|length }}
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>Заказов пока нет</p>
        {% endif %}
        <a href="/">На главную</a>
    </body>
    </html>
    '''
    return render_template_string(orders_html, orders=orders)


@app.route('/stats')
def stats_page():
    """HTML страница статистики"""
    stats = get_stats().json
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Статистика</title>
        <style>
            .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
            .stat-card { border: 1px solid #ccc; padding: 15px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>📊 Статистика магазина</h1>
        <div class="stats">
            <div class="stat-card">
                <h3>Товары</h3>
                <p>Всего товаров: {{ stats.total_products }}</p>
            </div>
            <div class="stat-card">
                <h3>Продажи</h3>
                <p>Всего заказов: {{ stats.total_orders }}</p>
                <p>Выручка: {{ stats.total_revenue }} руб.</p>
                <p>Продано единиц: {{ stats.total_items_sold }}</p>
            </div>
            <div class="stat-card">
                <h3>Аналитика</h3>
                <p>Популярная категория: {{ stats.most_popular_category }}</p>
                <p>Средний чек: {{ stats.average_order_value }} руб.</p>
            </div>
        </div>
        <a href="/">На главную</a>
    </body>
    </html>
    ''', stats=stats)


if __name__ == '__main__':
    app.run(debug=True, port=5000)