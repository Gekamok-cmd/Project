"""
Магазин принтеров - Flask приложение
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# ==================== МОДЕЛИ ====================

class Printer:
    """Класс принтера"""
    def __init__(self, id, name, printer_type, price, color, speed, stock):
        self.id = id
        self.name = name
        self.type = printer_type  # laser, inkjet, multifunctional
        self.price = price
        self.color = color  # True/False
        self.speed = speed  # страниц в минуту
        self.stock = stock

    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'price': self.price,
            'color': self.color,
            'speed': self.speed,
            'stock': self.stock
        }

# ==================== ДАННЫЕ ====================

# База данных принтеров
printers_db = [
    Printer(1, "HP LaserJet Pro M404dn", "laser", 25000, False, 40, 8),
    Printer(2, "Canon PIXMA G1420", "inkjet", 12000, True, 15, 12),
    Printer(3, "Epson L805", "inkjet", 32000, True, 12, 5),
    Printer(4, "Xerox B205", "laser", 18000, False, 35, 0),  # Нет в наличии
    Printer(5, "Brother HL-1212W", "laser", 15000, False, 20, 10),
    Printer(6, "HP OfficeJet Pro 8025", "multifunctional", 35000, True, 25, 6),
    Printer(7, "Canon i-SENSYS LBP623Cdw", "laser", 45000, True, 28, 3),
]

# Корзина пользователей (user_id: [items])
carts = {}

# Заказы
orders = []
order_counter = 1

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """Главная страница"""
    return '''
    <h1>🖨️ PrintMaster Printer Store</h1>
    <p>Best printers at best prices!</p>
    <h3>Available endpoints:</h3>
    <ul>
        <li><a href="/api/printers">All printers</a> (GET)</li>
        <li><a href="/api/printers/1">Printer by ID</a> (GET /api/printers/{id})</li>
        <li><a href="/api/printers/type/laser">Printers by type</a> (GET /api/printers/type/{type})</li>
        <li><a href="/api/printers/available">Only available</a> (GET)</li>
        <li><a href="/api/search?q=hp">Search printers</a> (GET /api/search?q=query)</li>
        <li><a href="/api/cart/1">User cart</a> (GET /api/cart/{user_id})</li>
        <li><a href="/api/stats">Store statistics</a> (GET)</li>
    </ul>
    <h3>API examples:</h3>
    <pre>
    # Add to cart:
    POST /api/cart/add
    {"user_id": 1, "printer_id": 1, "quantity": 1}

    # Checkout:
    POST /api/checkout
    {"user_id": 1}
    </pre>
    '''

@app.route('/api/printers', methods=['GET'])
def get_printers():
    """Получить все принтеры"""
    return jsonify([printer.to_dict() for printer in printers_db])

@app.route('/api/printers/<int:printer_id>', methods=['GET'])
def get_printer(printer_id):
    """Получить принтер по ID"""
    printer = next((p for p in printers_db if p.id == printer_id), None)
    if printer:
        return jsonify(printer.to_dict())
    return jsonify({'error': 'Принтер не найден'}), 404

@app.route('/api/printers/type/<string:printer_type>', methods=['GET'])
def get_printers_by_type(printer_type):
    """Получить принтеры по типу"""
    filtered = [p for p in printers_db if p.type == printer_type]
    return jsonify([p.to_dict() for p in filtered])

@app.route('/api/printers/available', methods=['GET'])
def get_available_printers():
    """Получить только принтеры в наличии"""
    available = [p for p in printers_db if p.stock > 0]
    return jsonify([p.to_dict() for p in available])

@app.route('/api/search', methods=['GET'])
def search_printers():
    """Поиск принтеров по названию"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'error': 'Укажите поисковый запрос'}), 400

    results = [p for p in printers_db if query in p.name.lower()]
    return jsonify([p.to_dict() for p in results])

@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    """Получить корзину пользователя"""
    if user_id not in carts:
        carts[user_id] = []

    cart_items = carts[user_id]
    total = sum(item['price'] * item['quantity'] for item in cart_items)

    return jsonify({
        'user_id': user_id,
        'items': cart_items,
        'total': total,
        'item_count': len(cart_items)
    })

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Добавить принтер в корзину"""
    data = request.get_json()

    # Проверка данных
    if not data:
        return jsonify({'error': 'Нет данных'}), 400

    required_fields = ['user_id', 'printer_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400

    user_id = data['user_id']
    printer_id = data['printer_id']
    quantity = data.get('quantity', 1)

    # Найти принтер
    printer = next((p for p in printers_db if p.id == printer_id), None)
    if not printer:
        return jsonify({'error': 'Принтер не найден'}), 404

    # Проверить наличие
    if printer.stock < quantity:
        return jsonify({'error': f'Недостаточно принтеров "{printer.name}" на складе'}), 400

    # Инициализировать корзину, если нужно
    if user_id not in carts:
        carts[user_id] = []

    # Проверить, есть ли уже такой принтер в корзине
    for item in carts[user_id]:
        if item['printer_id'] == printer_id:
            item['quantity'] += quantity
            break
    else:
        carts[user_id].append({
            'printer_id': printer_id,
            'name': printer.name,
            'price': printer.price,
            'quantity': quantity,
            'type': printer.type
        })

    return jsonify({
        'message': 'Принтер добавлен в корзину',
        'cart': carts[user_id]
    })

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Удалить принтер из корзины"""
    data = request.get_json()

    if not data or 'user_id' not in data or 'printer_id' not in data:
        return jsonify({'error': 'Нужны user_id и printer_id'}), 400

    user_id = data['user_id']
    printer_id = data['printer_id']

    if user_id not in carts:
        return jsonify({'error': 'Корзина не найдена'}), 404

    # Удалить принтер из корзины
    carts[user_id] = [item for item in carts[user_id] if item['printer_id'] != printer_id]

    return jsonify({
        'message': 'Принтер удален из корзины',
        'cart': carts[user_id]
    })

@app.route('/api/checkout', methods=['POST'])
def checkout():
    """Оформить заказ"""
    global order_counter

    data = request.get_json()

    if not data or 'user_id' not in data:
        return jsonify({'error': 'Нужен user_id'}), 400

    user_id = data['user_id']

    # Проверить корзину
    if user_id not in carts or not carts[user_id]:
        return jsonify({'error': 'Корзина пуста'}), 400

    # Проверить наличие всех товаров
    for item in carts[user_id]:
        printer = next((p for p in printers_db if p.id == item['printer_id']), None)
        if not printer or printer.stock < item['quantity']:
            return jsonify({'error': f'Недостаточно "{printer.name}" на складе'}), 400

    # Создать заказ
    order = {
        'order_id': order_counter,
        'user_id': user_id,
        'items': carts[user_id].copy(),
        'total': sum(item['price'] * item['quantity'] for item in carts[user_id]),
        'status': 'обрабатывается'
    }

    # Обновить остатки
    for item in carts[user_id]:
        printer = next(p for p in printers_db if p.id == item['printer_id'])
        printer.stock -= item['quantity']

    # Сохранить заказ
    orders.append(order)
    order_counter += 1

    # Очистить корзину
    carts[user_id] = []

    return jsonify({
        'message': 'Заказ успешно оформлен',
        'order': order
    })

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получить все заказы (для администратора)"""
    return jsonify(orders)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Получить заказ по ID"""
    order = next((o for o in orders if o['order_id'] == order_id), None)
    if order:
        return jsonify(order)
    return jsonify({'error': 'Заказ не найден'}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Статистика магазина"""
    total_printers = len(printers_db)
    available_printers = sum(1 for p in printers_db if p.stock > 0)
    total_stock = sum(p.stock for p in printers_db)
    total_orders = len(orders)
    total_revenue = sum(order['total'] for order in orders)

    # Статистика по типам
    type_stats = {}
    for printer in printers_db:
        if printer.type not in type_stats:
            type_stats[printer.type] = {'count': 0, 'stock': 0}
        type_stats[printer.type]['count'] += 1
        type_stats[printer.type]['stock'] += printer.stock

    # Самый популярный тип в заказах
    popular_types = {}
    for order in orders:
        for item in order['items']:
            printer = next(p for p in printers_db if p.id == item['printer_id'])
            popular_types[printer.type] = popular_types.get(printer.type, 0) + item['quantity']

    most_popular = max(popular_types.items(), key=lambda x: x[1])[0] if popular_types else 'нет заказов'

    return jsonify({
        'store_name': 'PrintMaster',
        'total_printers': total_printers,
        'available_printers': available_printers,
        'total_stock': total_stock,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'type_statistics': type_stats,
        'most_popular_type': most_popular,
        'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0
    })

@app.route('/api/admin/add_printer', methods=['POST'])
def add_printer():
    """Добавить новый принтер (админ)"""
    data = request.get_json()

    required_fields = ['name', 'type', 'price', 'color', 'speed', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400

    # Генерируем ID
    new_id = max(p.id for p in printers_db) + 1 if printers_db else 1

    # Создаем принтер
    printer = Printer(
        id=new_id,
        name=data['name'],
        printer_type=data['type'],
        price=data['price'],
        color=data['color'],
        speed=data['speed'],
        stock=data['stock']
    )

    printers_db.append(printer)

    return jsonify({
        'message': 'Принтер добавлен',
        'printer': printer.to_dict()
    }), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)