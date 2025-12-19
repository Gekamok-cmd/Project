"""
Интеграционные тесты API магазина принтеров
"""

import pytest
import json
from app import app, printers_db, carts, orders

@pytest.fixture
def client():
    """Фикстура для тестового клиента Flask"""
    app.config['TESTING'] = True

    # Сохраняем исходное состояние
    original_printers = printers_db.copy()
    original_carts = carts.copy()
    original_orders = orders.copy()

    with app.test_client() as client:
        # Сбрасываем глобальные переменные
        carts.clear()
        orders.clear()
        yield client

    # Восстанавливаем исходное состояние
    printers_db.clear()
    printers_db.extend(original_printers)

    carts.clear()
    carts.update(original_carts)

    orders.clear()
    orders.extend(original_orders)

class TestPrinterStoreAPI:
    """Тесты API магазина принтеров"""

    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get('/')
        assert response.status_code == 200
        # Используем английский текст для проверки
        assert b'PrintMaster' in response.data

    def test_get_all_printers(self, client):
        """Тест получения всех принтеров"""
        response = client.get('/api/printers')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 7  # У нас 7 принтеров в базе

        # Проверяем структуру первого принтера
        first_printer = data[0]
        required_fields = ['id', 'name', 'type', 'price', 'color', 'speed', 'stock']
        for field in required_fields:
            assert field in first_printer

    def test_get_printer_by_id(self, client):
        """Тест получения принтера по ID"""
        response = client.get('/api/printers/1')
        assert response.status_code == 200

        printer = response.get_json()
        assert printer['id'] == 1
        assert 'HP' in printer['name']
        assert printer['type'] == "laser"

    def test_get_nonexistent_printer(self, client):
        """Тест получения несуществующего принтера"""
        response = client.get('/api/printers/999')
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_get_printers_by_type(self, client):
        """Тест получения принтеров по типу"""
        response = client.get('/api/printers/type/laser')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

        # Проверяем, что все принтеры лазерные
        for printer in data:
            assert printer['type'] == 'laser'

    def test_get_available_printers(self, client):
        """Тест получения только доступных принтеров"""
        response = client.get('/api/printers/available')
        assert response.status_code == 200

        data = response.get_json()

        # Проверяем, что все принтеры в наличии
        for printer in data:
            assert printer['stock'] > 0

        # Принтер с ID 4 должен отсутствовать (stock = 0)
        printer_ids = [p['id'] for p in data]
        assert 4 not in printer_ids

    def test_search_printers(self, client):
        """Тест поиска принтеров"""
        # Поиск по бренду HP
        response = client.get('/api/search?q=hp')
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1
        assert any('HP' in printer['name'] for printer in data)

    def test_search_empty_query(self, client):
        """Тест поиска с пустым запросом"""
        response = client.get('/api/search?q=')
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_cart_operations(self, client):
        """Тест операций с корзиной"""
        user_id = 100

        # 1. Получить пустую корзину
        response = client.get(f'/api/cart/{user_id}')
        assert response.status_code == 200

        cart_data = response.get_json()
        assert cart_data['user_id'] == user_id
        assert cart_data['items'] == []
        assert cart_data['total'] == 0

        # 2. Добавить принтер в корзину
        response = client.post('/api/cart/add',
                             data=json.dumps({
                                 'user_id': user_id,
                                 'printer_id': 1,
                                 'quantity': 2
                             }),
                             content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert len(data['cart']) == 1
        assert data['cart'][0]['printer_id'] == 1
        assert data['cart'][0]['quantity'] == 2

        # 3. Проверить корзину через GET
        response = client.get(f'/api/cart/{user_id}')
        cart_data = response.get_json()
        assert cart_data['total'] == 50000  # 25000 * 2

        # 4. Удалить принтер из корзины
        response = client.post('/api/cart/remove',
                             data=json.dumps({
                                 'user_id': user_id,
                                 'printer_id': 1
                             }),
                             content_type='application/json')

        assert response.status_code == 200

        # 5. Проверить, что корзина пуста
        response = client.get(f'/api/cart/{user_id}')
        cart_data = response.get_json()
        assert cart_data['items'] == []

    def test_add_nonexistent_printer_to_cart(self, client):
        """Тест добавления несуществующего принтера в корзину"""
        response = client.post('/api/cart/add',
                             data=json.dumps({
                                 'user_id': 1,
                                 'printer_id': 999
                             }),
                             content_type='application/json')

        assert response.status_code == 404

    def test_add_out_of_stock_printer_to_cart(self, client):
        """Тест добавления отсутствующего принтера в корзину"""
        # Принтер с ID 4 имеет stock = 0
        response = client.post('/api/cart/add',
                             data=json.dumps({
                                 'user_id': 1,
                                 'printer_id': 4,
                                 'quantity': 1
                             }),
                             content_type='application/json')

        assert response.status_code == 400

    def test_checkout_flow(self, client):
        """Тест полного процесса оформления заказа"""
        user_id = 200

        # 1. Получить начальный остаток
        response = client.get('/api/printers/1')
        initial_stock = response.get_json()['stock']

        # 2. Добавить в корзину
        response = client.post('/api/cart/add',
                             data=json.dumps({
                                 'user_id': user_id,
                                 'printer_id': 1,
                                 'quantity': 1
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        # 3. Оформить заказ
        response = client.post('/api/checkout',
                             data=json.dumps({'user_id': user_id}),
                             content_type='application/json')

        assert response.status_code == 200

        data = response.get_json()
        assert 'message' in data
        assert data['order']['user_id'] == user_id
        assert data['order']['total'] == 25000

        # 4. Проверить, что остаток уменьшился
        response = client.get('/api/printers/1')
        final_stock = response.get_json()['stock']
        assert final_stock == initial_stock - 1

        # 5. Проверить, что корзина очистилась
        response = client.get(f'/api/cart/{user_id}')
        cart_data = response.get_json()
        assert cart_data['items'] == []

        # 6. Проверить, что заказ в списке
        response = client.get('/api/orders')
        orders_list = response.get_json()
        assert len(orders_list) == 1

    def test_checkout_empty_cart(self, client):
        """Тест оформления пустой корзины"""
        response = client.post('/api/checkout',
                             data=json.dumps({'user_id': 999}),
                             content_type='application/json')

        assert response.status_code == 400

    def test_get_orders(self, client):
        """Тест получения списка заказов"""
        # Сначала создаем заказ
        user_id = 300
        client.post('/api/cart/add',
                   data=json.dumps({'user_id': user_id, 'printer_id': 1}),
                   content_type='application/json')
        client.post('/api/checkout',
                   data=json.dumps({'user_id': user_id}),
                   content_type='application/json')

        response = client.get('/api/orders')
        assert response.status_code == 200

        orders_list = response.get_json()
        assert isinstance(orders_list, list)
        assert len(orders_list) == 1

    def test_get_order_by_id(self, client):
        """Тест получения заказа по ID"""
        # Создаем заказ
        user_id = 400
        client.post('/api/cart/add',
                   data=json.dumps({'user_id': user_id, 'printer_id': 1}),
                   content_type='application/json')
        response = client.post('/api/checkout',
                             data=json.dumps({'user_id': user_id}),
                             content_type='application/json')

        order_id = response.get_json()['order']['order_id']

        # Получаем заказ по ID
        response = client.get(f'/api/orders/{order_id}')
        assert response.status_code == 200

        order = response.get_json()
        assert order['order_id'] == order_id

    def test_get_stats(self, client):
        """Тест получения статистики"""
        response = client.get('/api/stats')
        assert response.status_code == 200

        stats = response.get_json()
        required_fields = [
            'store_name', 'total_printers', 'available_printers',
            'total_stock', 'total_orders', 'total_revenue',
            'type_statistics', 'most_popular_type', 'average_order_value'
        ]

        for field in required_fields:
            assert field in stats

        assert stats['store_name'] == 'PrintMaster'
        assert stats['total_printers'] == 7

    def test_add_new_printer(self, client):
        """Тест добавления нового принтера"""
        new_printer = {
            'name': 'Test Printer X1000',
            'type': 'laser',
            'price': 30000,
            'color': True,
            'speed': 45,
            'stock': 10
        }

        response = client.post('/api/admin/add_printer',
                             data=json.dumps(new_printer),
                             content_type='application/json')

        assert response.status_code == 201

        data = response.get_json()
        assert data['message'] == 'Принтер добавлен'
        assert data['printer']['name'] == 'Test Printer X1000'

        # Проверить, что принтер действительно добавлен
        response = client.get('/api/printers')
        printers = response.get_json()
        assert len(printers) == 8  # Было 7, стало 8

    def test_add_printer_invalid_data(self, client):
        """Тест добавления принтера с невалидными данными"""
        response = client.post('/api/admin/add_printer',
                             data=json.dumps({'name': 'Test'}),
                             content_type='application/json')

        assert response.status_code == 400

if __name__ == '__main__':
    pytest.main([__file__, '-v'])