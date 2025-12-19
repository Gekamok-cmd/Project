from flask import Flask, jsonify, request

app = Flask(__name__)

# База данных принтеров в памяти
printers = [
    {
        'id': 1,
        'name': 'HP LaserJet Pro M404',
        'type': 'лазерный',
        'price': 15000,
        'color': False,
        'speed': 40,
        'stock': 5,
        'rating': 4.5
    },
    {
        'id': 2,
        'name': 'Canon PIXMA G1420',
        'type': 'струйный',
        'price': 8000,
        'color': True,
        'speed': 10,
        'stock': 8,
        'rating': 4.2
    },
    {
        'id': 3,
        'name': 'Epson L805',
        'type': 'струйный',
        'price': 22000,
        'color': True,
        'speed': 15,
        'stock': 3,
        'rating': 4.7
    },
    {
        'id': 4,
        'name': 'Xerox B205',
        'type': 'лазерный',
        'price': 12000,
        'color': False,
        'speed': 35,
        'stock': 0,
        'rating': 4.0
    },
    {
        'id': 5,
        'name': 'Brother HL-1212W',
        'type': 'лазерный',
        'price': 9000,
        'color': False,
        'speed': 20,
        'stock': 10,
        'rating': 4.3
    }
]

# Корзина пользователей (упрощенно)
carts = {}
orders = []
order_id_counter = 1


@app.route('/')
def home():
    """Главная страница магазина"""
    return """
    <h1>🖨️ Магазин принтеров</h1>
    <p>Лучшие принтеры по лучшим ценам!</p>
    <ul>
        <li><a href="/api/printers">Все принтеры (JSON)</a></li>
        <li><a href="/api/printers?type=лазерный">Только лазерные</a></li>
        <li><a href="/api/printers?type=струйный">Только струйные</a></li>
        <li><a href="/api/printers/available">В наличии</a></li>
        <li><a href="/stats">Статистика магазина</a></li>
        <li><a href="/cart/1">Корзина (пример)</a></li>
    </ul>
    """


@app.route('/api/printers')
def get_printers():
    """Получить список всех принтеров с фильтрацией"""
    filtered_printers = printers.copy()

    # Фильтрация по типу
    printer_type = request.args.get('type')
    if printer_type:
        filtered_printers = [p for p in filtered_printers if p['type'] == printer_type]

    # Фильтрация по наличию цвета
    color = request.args.get('color')
    if color is not None:
        color_bool = color.lower() == 'true'
        filtered_printers = [p for p in filtered_printers if p['color'] == color_bool]

    # Фильтрация по цене
    max_price = request.args.get('max_price')
    if max_price:
        filtered_printers = [p for p in filtered_printers if p['price'] <= int(max_price)]

    # Сортировка
    sort_by = request.args.get('sort', 'id')
    if sort_by in ['price', 'speed', 'rating', 'stock']:
        filtered_printers.sort(key=lambda x: x[sort_by])

    return jsonify(filtered_printers)


@app.route('/api/printers/available')
def get_available_printers():
    """Получить только принтеры в наличии"""
    available = [p for p in printers if p['stock'] > 0]
    return jsonify(available)


@app.route('/api/printer/<int:printer_id>')
def get_printer(printer_id):
    """Получить принтер по ID"""
    printer = next((p for p in printers if p['id'] == printer_id), None)

    if printer:
        return jsonify(printer)
    return jsonify({'error': 'Принтер не найден'}), 404


@app.route('/api/search')
def search_printers():
    """Поиск принтеров по названию"""
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'error': 'Нет поискового запроса'}), 400

    results = [p for p in printers if query in p['name'].lower()]
    return jsonify(results)


@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    """Получить корзину пользователя"""
    if user_id not in carts:
        carts[user_id] = []

    return jsonify({
        'user_id': user_id,
        'items': carts[user_id],
        'total': sum(item['price'] * item['quantity'] for item in carts[user_id])
    })


@app.route('/api/cart/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    """Добавить принтер в корзину"""
    data = request.get_json()

    if not data or 'printer_id' not in data:
        return jsonify({'error': 'Нужен printer_id'}), 400

    printer_id = data['printer_id']
    quantity = data.get('quantity', 1)

    printer = next((p for p in printers if p['id'] == printer_id), None)
    if not printer:
        return jsonify({'error': 'Принтер не найден'}), 404

    if printer['stock'] < quantity:
        return jsonify({'error': 'Недостаточно товара на складе'}), 400

    if user_id not in carts:
        carts[user_id] = []

    # Проверяем, есть ли уже такой принтер в корзине
    for item in carts[user_id]:
        if item['printer_id'] == printer_id:
            item['quantity'] += quantity
            break
    else:
        carts[user_id].append({
            'printer_id': printer_id,
            'name': printer['name'],
            'price': printer['price'],
            'quantity': quantity
        })

    return jsonify({
        'message': 'Принтер добавлен в корзину',
        'cart': carts[user_id]
    })


@app.route('/api/cart/<int:user_id>/remove', methods=['POST'])
def remove_from_cart(user_id):
    """Удалить принтер из корзины"""
    data = request.get_json()

    if not data or 'printer_id' not in data:
        return jsonify({'error': 'Нужен printer_id'}), 400

    if user_id not in carts:
        return jsonify({'error': 'Корзина пуста'}), 400

    printer_id = data['printer_id']
    carts[user_id] = [item for item in carts[user_id] if item['printer_id'] != printer_id]

    return jsonify({
        'message': 'Принтер удален из корзины',
        'cart': carts[user_id]
    })


@app.route('/api/cart/<int:user_id>/checkout', methods=['POST'])
def checkout(user_id):
    """Оформить заказ"""
    global order_id_counter

    if user_id not in carts or not carts[user_id]:
        return jsonify({'error': 'Корзина пуста'}), 400

    # Проверяем наличие товаров
    for item in carts[user_id]:
        printer = next((p for p in printers if p['id'] == item['printer_id']), None)
        if not printer or printer['stock'] < item['quantity']:
            return jsonify({'error': f'Недостаточно {printer["name"]} на складе'}), 400

    # Создаем заказ
    order = {
        'order_id': order_id_counter,
        'user_id': user_id,
        'items': carts[user_id].copy(),
        'total': sum(item['price'] * item['quantity'] for item in carts[user_id]),
        'status': 'обрабатывается'
    }

    # Обновляем остатки
    for item in carts[user_id]:
        printer = next((p for p in printers if p['id'] == item['printer_id']))
        printer['stock'] -= item['quantity']

    orders.append(order)
    order_id_counter += 1

    # Очищаем корзину
    carts[user_id] = []

    return jsonify({
        'message': 'Заказ оформлен',
        'order': order
    })


@app.route('/api/orders')
def get_orders():
    """Получить все заказы (для админа)"""
    return jsonify(orders)


@app.route('/api/order/<int:order_id>')
def get_order(order_id):
    """Получить заказ по ID"""
    order = next((o for o in orders if o['order_id'] == order_id), None)

    if order:
        return jsonify(order)
    return jsonify({'error': 'Заказ не найден'}), 404


@app.route('/api/stats')
def get_stats():
    """Статистика магазина"""
    total_printers = len(printers)
    available_printers = sum(1 for p in printers if p['stock'] > 0)
    total_stock = sum(p['stock'] for p in printers)
    total_orders = len(orders)
    total_revenue = sum(order['total'] for order in orders)

    # Самый популярный тип
    types = {}
    for order in orders:
        for item in order['items']:
            printer = next((p for p in printers if p['id'] == item['printer_id']))
            types[printer['type']] = types.get(printer['type'], 0) + item['quantity']

    most_popular_type = max(types.items(), key=lambda x: x[1])[0] if types else 'нет заказов'

    return jsonify({
        'total_printers': total_printers,
        'available_printers': available_printers,
        'total_stock': total_stock,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'most_popular_type': most_popular_type,
        'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0
    })


@app.route('/stats')
def stats_page():
    """HTML страница статистики"""
    stats = get_stats().json

    html = f"""
    <h1>📊 Статистика магазина принтеров</h1>
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
        <div style="border: 1px solid #ccc; padding: 15px; border-radius: 8px;">
            <h3>Товары</h3>
            <p>Всего принтеров: {stats['total_printers']}</p>
            <p>В наличии: {stats['available_printers']}</p>
            <p>Общий остаток: {stats['total_stock']}</p>
        </div>

        <div style="border: 1px solid #ccc; padding: 15px; border-radius: 8px;">
            <h3>Продажи</h3>
            <p>Всего заказов: {stats['total_orders']}</p>
            <p>Общая выручка: {stats['total_revenue']} ₽</p>
            <p>Средний чек: {stats['average_order_value']} ₽</p>
        </div>

        <div style="border: 1px solid #ccc; padding: 15px; border-radius: 8px; grid-column: span 2;">
            <h3>Аналитика</h3>
            <p>Самый популярный тип: {stats['most_popular_type']}</p>
        </div>
    </div>
    <a href="/">На главную</a>
    """
    return html


@app.route('/api/add_printer', methods=['POST'])
def add_printer():
    """Добавить новый принтер (для админа)"""
    data = request.get_json()

    required_fields = ['name', 'type', 'price', 'color', 'speed', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400

    new_id = max(p['id'] for p in printers) + 1 if printers else 1

    new_printer = {
        'id': new_id,
        'name': data['name'],
        'type': data['type'],
        'price': data['price'],
        'color': data['color'],
        'speed': data['speed'],
        'stock': data['stock'],
        'rating': data.get('rating', 0)
    }

    printers.append(new_printer)

    return jsonify({
        'message': 'Принтер добавлен',
        'printer': new_printer
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)