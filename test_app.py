import json
import pytest
import requests
import time
import subprocess
import os
import signal
from app import app, printers, carts, orders


# === МОДУЛЬНЫЕ ТЕСТЫ ===
def test_printer_data_structure():
    """Тест структуры данных принтеров"""
    assert len(printers) > 0

    printer = printers[0]
    required_fields = ['id', 'name', 'type', 'price', 'color', 'speed', 'stock', 'rating']
    for field in required_fields:
        assert field in printer


def test_printer_types():
    """Тест типов принтеров"""
    valid_types = {'лазерный', 'струйный'}
    for printer in printers:
        assert printer['type'] in valid_types


# === ИНТЕГРАЦИОННЫЕ ТЕСТЫ ===
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Сбрасываем состояние перед каждым тестом
        carts.clear()
        orders.clear()
        yield client


def test_home_page(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Магазин принтеров' in response.data


def test_get_all_printers(client):
    """Тест получения всех принтеров"""
    response = client.get('/api/printers')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 5
    assert data[0]['name'] == 'HP LaserJet Pro M404'


def test_filter_printers_by_type(client):
    """Тест фильтрации по типу принтера"""
    response = client.get('/api/printers?type=лазерный')
    assert response.status_code == 200

    data = response.get_json()
    for printer in data:
        assert printer['type'] == 'лазерный'


def test_filter_printers_by_color(client):
    """Тест фильтрации по цвету"""
    response = client.get('/api/printers?color=true')
    assert response.status_code == 200

    data = response.get_json()
    for printer in data:
        assert printer['color'] == True


def test_filter_printers_by_price(client):
    """Тест фильтрации по цене"""
    response = client.get('/api/printers?max_price=10000')
    assert response.status_code == 200

    data = response.get_json()
    for printer in data:
        assert printer['price'] <= 10000


def test_get_available_printers(client):
    """Тест получения только доступных принтеров"""
    response = client.get('/api/printers/available')
    assert response.status_code == 200

    data = response.get_json()
    for printer in data:
        assert printer['stock'] > 0


def test_get_printer_by_id(client):
    """Тест получения принтера по ID"""
    response = client.get('/api/printer/1')
    assert response.status_code == 200

    printer = response.get_json()
    assert printer['id'] == 1
    assert printer['name'] == 'HP LaserJet Pro M404'


def test_get_nonexistent_printer(client):
    """Тест получения несуществующего принтера"""
    response = client.get('/api/printer/999')
    assert response.status_code == 404
    assert 'error' in response.get_json()


def test_search_printers(client):
    """Тест поиска принтеров"""
    response = client.get('/api/search?q=hp')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) > 0
    assert 'HP' in data[0]['name']


def test_search_empty_query(client):
    """Тест поиска с пустым запросом"""
    response = client.get('/api/search?q=')
    assert response.status_code == 400


def test_cart_operations(client):
    """Тест операций с корзиной"""
    user_id = 100

    # 1. Получить пустую корзину
    response = client.get(f'/api/cart/{user_id}')
    assert response.status_code == 200
    cart = response.get_json()
    assert cart['items'] == []
    assert cart['total'] == 0

    # 2. Добавить принтер в корзину
    response = client.post(
        f'/api/cart/{user_id}/add',
        json={'printer_id': 1, 'quantity': 2}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Принтер добавлен в корзину'
    assert len(data['cart']) == 1

    # 3. Проверить обновленную корзину
    response = client.get(f'/api/cart/{user_id}')
    cart = response.get_json()
    assert len(cart['items']) == 1
    assert cart['total'] == 30000  # 2 * 15000

    # 4. Удалить принтер из корзины
    response = client.post(
        f'/api/cart/{user_id}/remove',
        json={'printer_id': 1}
    )
    assert response.status_code == 200

    # 5. Проверить, что корзина пуста
    response = client.get(f'/api/cart/{user_id}')
    cart = response.get_json()
    assert len(cart['items']) == 0


def test_add_nonexistent_printer_to_cart(client):
    """Тест добавления несуществующего принтера в корзину"""
    response = client.post(
        '/api/cart/1/add',
        json={'printer_id': 999}
    )
    assert response.status_code == 404


def test_add_out_of_stock_printer(client):
    """Тест добавления отсутствующего принтера в корзину"""
    # Принтер с ID 4 имеет stock = 0
    response = client.post(
        '/api/cart/1/add',
        json={'printer_id': 4, 'quantity': 1}
    )
    assert response.status_code == 400


def test_checkout_flow(client):
    """Тест полного процесса оформления заказа"""
    user_id = 200

    # 1. Добавить принтер в корзину
    initial_stock = next(p['stock'] for p in printers if p['id'] == 1)

    response = client.post(
        f'/api/cart/{user_id}/add',
        json={'printer_id': 1, 'quantity': 1}
    )
    assert response.status_code == 200

    # 2. Оформить заказ
    response = client.post(f'/api/cart/{user_id}/checkout')
    assert response.status_code == 200

    data = response.get_json()
    assert data['message'] == 'Заказ оформлен'
    assert data['order']['user_id'] == user_id
    assert len(data['order']['items']) == 1

    # 3. Проверить, что остаток уменьшился
    final_stock = next(p['stock'] for p in printers if p['id'] == 1)
    assert final_stock == initial_stock - 1

    # 4. Проверить, что корзина очистилась
    response = client.get(f'/api/cart/{user_id}')
    cart = response.get_json()
    assert len(cart['items']) == 0

    # 5. Проверить, что заказ в списке
    response = client.get('/api/orders')
    orders_list = response.get_json()
    assert len(orders_list) == 1


def test_checkout_empty_cart(client):
    """Тест оформления пустой корзины"""
    response = client.post('/api/cart/999/checkout')
    assert response.status_code == 400


def test_get_order_by_id(client):
    """Тест получения заказа по ID"""
    # Сначала создаем заказ
    user_id = 300
    client.post(f'/api/cart/{user_id}/add', json={'printer_id': 1})
    client.post(f'/api/cart/{user_id}/checkout')

    response = client.get('/api/order/1')
    assert response.status_code == 200

    order = response.get_json()
    assert order['order_id'] == 1
    assert order['status'] == 'обрабатывается'


def test_get_stats(client):
    """Тест получения статистики"""
    response = client.get('/api/stats')
    assert response.status_code == 200

    stats = response.get_json()
    assert 'total_printers' in stats
    assert 'total_revenue' in stats
    assert 'most_popular_type' in stats


def test_stats_page(client):
    """Тест HTML страницы статистики"""
    response = client.get('/stats')
    assert response.status_code == 200
    assert b'Статистика магазина' in response.data


def test_add_new_printer(client):
    """Тест добавления нового принтера"""
    new_printer = {
        'name': 'Test Printer',
        'type': 'лазерный',
        'price': 5000,
        'color': False,
        'speed': 25,
        'stock': 10,
        'rating': 4.0
    }

    response = client.post('/api/add_printer', json=new_printer)
    assert response.status_code == 201

    data = response.get_json()
    assert data['message'] == 'Принтер добавлен'
    assert data['printer']['name'] == 'Test Printer'

    # Проверить, что принтер действительно добавлен
    response = client.get('/api/printers')
    printers_list = response.get_json()
    assert len(printers_list) == 6


def test_add_printer_invalid_data(client):
    """Тест добавления принтера с невалидными данными"""
    response = client.post('/api/add_printer', json={'name': 'Test'})
    assert response.status_code == 400


# === СИСТЕМНЫЕ ТЕСТЫ (E2E) ===
class TestPrinterShopSystem:
    """Системные тесты магазина принтеров"""

    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Запуск тестового сервера"""
        self.port = 5998
        self.base_url = f"http://localhost:{self.port}"

        # Запускаем сервер
        self.server_process = subprocess.Popen(
            ['python', 'app.py'],
            env={**os.environ, 'FLASK_RUN_PORT': str(self.port)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # Ждем запуска
        time.sleep(2)

        yield

        # Останавливаем
        os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
        self.server_process.wait()

    def test_system_availability(self):
        """Тест доступности системы"""
        response = requests.get(f"{self.base_url}/", timeout=5)
        assert response.status_code == 200
        assert 'Магазин принтеров' in response.text

    def test_full_shopping_journey(self):
        """Полный путь покупателя"""
        user_id = 500

        # 1. Смотрим все принтеры
        response = requests.get(f"{self.base_url}/api/printers")
        assert response.status_code == 200
        initial_printers = response.json()

        # 2. Фильтруем лазерные принтеры
        response = requests.get(f"{self.base_url}/api/printers?type=лазерный")
        laser_printers = response.json()
        for printer in laser_printers:
            assert printer['type'] == 'лазерный'

        # 3. Ищем конкретный принтер
        hp_printer = next(p for p in initial_printers if 'HP' in p['name'])
        assert hp_printer is not None

        # 4. Добавляем в корзину
        response = requests.post(
            f"{self.base_url}/api/cart/{user_id}/add",
            json={'printer_id': hp_printer['id'], 'quantity': 1}
        )
        assert response.status_code == 200

        # 5. Проверяем корзину
        response = requests.get(f"{self.base_url}/api/cart/{user_id}")
        cart = response.json()
        assert len(cart['items']) == 1

        # 6. Оформляем заказ
        response = requests.post(f"{self.base_url}/api/cart/{user_id}/checkout")
        assert response.status_code == 200

        order = response.json()['order']
        assert order['total'] == hp_printer['price']

        # 7. Проверяем статистику
        response = requests.get(f"{self.base_url}/api/stats")
        stats = response.json()
        assert stats['total_orders'] >= 1
        assert stats['total_revenue'] >= hp_printer['price']

    def test_concurrent_operations(self):
        """Тест конкурентных операций"""
        import threading

        results = []

        def make_purchase(user_id):
            try:
                # Добавляем и оформляем заказ
                requests.post(
                    f"{self.base_url}/api/cart/{user_id}/add",
                    json={'printer_id': 5, 'quantity': 1}
                )
                response = requests.post(f"{self.base_url}/api/cart/{user_id}/checkout")
                results.append(response.status_code)
            except:
                results.append(0)

        # 3 параллельных покупки
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_purchase, args=(600 + i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Все операции должны быть успешными
        assert all(status == 200 for status in results)

        # Проверяем, что остатки уменьшились правильно
        response = requests.get(f"{self.base_url}/api/printer/5")
        printer = response.json()
        assert printer['stock'] <= 7  # Изначально было 10

    def test_error_scenarios(self):
        """Тест различных сценариев ошибок"""
        # Несуществующий принтер
        response = requests.get(f"{self.base_url}/api/printer/9999")
        assert response.status_code == 404

        # Пустой поиск
        response = requests.get(f"{self.base_url}/api/search?q=")
        assert response.status_code == 400

        # Оформление пустой корзины
        response = requests.post(f"{self.base_url}/api/cart/999/checkout")
        assert response.status_code == 400

    def test_performance(self):
        """Тест производительности"""
        import time

        endpoints = [
            '/',
            '/api/printers',
            '/api/stats',
            '/stats'
        ]

        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            end = time.time()

            response_time = end - start
            assert response.status_code == 200
            assert response_time < 1.0, f"Медленный ответ: {response_time:.2f}с"

    def test_data_integrity(self):
        """Тест целостности данных"""
        # 1. Получаем принтеры
        response = requests.get(f"{self.base_url}/api/printers")
        printers = response.json()
        printer_ids = {p['id'] for p in printers}

        # 2. Для каждого ID проверяем доступность
        for printer_id in printer_ids:
            response = requests.get(f"{self.base_url}/api/printer/{printer_id}")
            assert response.status_code == 200
            printer = response.json()
            assert printer['id'] == printer_id

    def test_cart_isolation(self):
        """Тест изоляции корзин разных пользователей"""
        user1_id = 700
        user2_id = 701

        # Добавляем в корзину user1
        requests.post(
            f"{self.base_url}/api/cart/{user1_id}/add",
            json={'printer_id': 1}
        )

        # Корзина user2 должна быть пуста
        response = requests.get(f"{self.base_url}/api/cart/{user2_id}")
        cart2 = response.json()
        assert len(cart2['items']) == 0

        # Корзина user1 не пуста
        response = requests.get(f"{self.base_url}/api/cart/{user1_id}")
        cart1 = response.json()
        assert len(cart1['items']) == 1


# === ЗАПУСК ТЕСТОВ ===
if __name__ == '__main__':
    import sys

    sys.exit(pytest.main([__file__, '-v']))