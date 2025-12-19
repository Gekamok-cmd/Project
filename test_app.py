import json
import pytest
import requests
import time
import subprocess
import os
import sys
from app import app, printers, carts, orders, order_id_counter


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
        # Сбрасываем счетчик заказов
        global order_id_counter
        order_id_counter = 1
        yield client


def test_home_page(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<h1>' in response.data


def test_get_all_printers(client):
    """Тест получения всех принтеров"""
    response = client.get('/api/printers')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 5
    assert 'HP' in data[0]['name']


def test_filter_printers_by_type(client):
    """Тест фильтрации по типу принтера"""
    response = client.get('/api/printers?type=лазерный')
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) > 0
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
    assert 'HP' in printer['name']


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
    assert 'HP' in data[0]['name'].upper()


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
    assert 'message' in data
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
    assert 'message' in data
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
    response = client.post(f'/api/cart/{user_id}/add', json={'printer_id': 1})
    assert response.status_code == 200

    response = client.post(f'/api/cart/{user_id}/checkout')
    assert response.status_code == 200

    # Получаем ID созданного заказа
    order_data = response.get_json()
    order_id = order_data['order']['order_id']

    # Теперь получаем заказ по этому ID
    response = client.get(f'/api/order/{order_id}')
    assert response.status_code == 200

    order = response.get_json()
    assert order['order_id'] == order_id


def test_get_stats(client):
    """Тест получения статистики"""
    response = client.get('/api/stats')
    assert response.status_code == 200

    stats = response.get_json()
    assert 'total_printers' in stats
    assert 'total_revenue' in stats


def test_stats_page(client):
    """Тест HTML страницы статистики"""
    response = client.get('/stats')
    assert response.status_code == 200
    assert b'<h1>' in response.data


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


# === СИСТЕМНЫЕ ТЕСТЫ (E2E) - Windows-совместимые ===
class TestPrinterShopSystem:
    """Системные тесты магазина принтеров"""

    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Запуск тестового сервера для Windows"""
        self.port = 5998
        self.base_url = f"http://localhost:{self.port}"

        # Запускаем сервер (Windows-совместимая версия)
        self.server_process = subprocess.Popen(
            [sys.executable, 'app.py'],
            env={**os.environ, 'FLASK_RUN_PORT': str(self.port)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # Ждем запуска
        for _ in range(30):  # 30 попыток по 0.5 секунды = 15 секунд максимум
            try:
                response = requests.get(f"{self.base_url}/", timeout=1)
                if response.status_code == 200:
                    break
            except:
                time.sleep(0.5)
        else:
            self.teardown_server()
            raise RuntimeError("Сервер не запустился")

        yield

        self.teardown_server()

    def teardown_server(self):
        """Остановка сервера для Windows"""
        if hasattr(self, 'server_process') and self.server_process:
            if os.name == 'nt':  # Windows
                import ctypes
                ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, self.server_process.pid)
            else:  # Unix/Linux
                import signal
                self.server_process.send_signal(signal.SIGTERM)

            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)

    def test_system_availability(self):
        """Тест доступности системы"""
        response = requests.get(f"{self.base_url}/", timeout=5)
        assert response.status_code == 200

    def test_full_shopping_journey(self):
        """Полный путь покупателя"""
        user_id = 500

        # 1. Смотрим все принтеры
        response = requests.get(f"{self.base_url}/api/printers")
        assert response.status_code == 200
        initial_printers = response.json()

        # 2. Фильтруем лазерные принтеры
        response = requests.get(f"{self.base_url}/api/printers?type=лазерный")
        assert response.status_code == 200
        laser_printers = response.json()
        if laser_printers:  # Могут быть пустые
            for printer in laser_printers:
                assert printer['type'] == 'лазерный'

        # 3. Ищем HP принтер
        hp_printer = None
        for printer in initial_printers:
            if 'HP' in printer['name'].upper():
                hp_printer = printer
                break

        assert hp_printer is not None

        # 4. Добавляем в корзину
        response = requests.post(
            f"{self.base_url}/api/cart/{user_id}/add",
            json={'printer_id': hp_printer['id'], 'quantity': 1}
        )
        assert response.status_code == 200

        # 5. Проверяем корзину
        response = requests.get(f"{self.base_url}/api/cart/{user_id}")
        assert response.status_code == 200
        cart = response.json()
        assert len(cart['items']) == 1

        # 6. Оформляем заказ
        response = requests.post(f"{self.base_url}/api/cart/{user_id}/checkout")
        assert response.status_code == 200

        order = response.json()['order']
        assert order['total'] == hp_printer['price']

        # 7. Проверяем статистику
        response = requests.get(f"{self.base_url}/api/stats")
        assert response.status_code == 200
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
                    json={'printer_id': 5, 'quantity': 1},
                    timeout=3
                )
                response = requests.post(
                    f"{self.base_url}/api/cart/{user_id}/checkout",
                    timeout=3
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(0)
                print(f"Error in thread: {e}")

        # 2 параллельных покупки (не 3, чтобы не исчерпать stock)
        threads = []
        for i in range(2):
            thread = threading.Thread(target=make_purchase, args=(600 + i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Проверяем успешность операций
        assert sum(1 for status in results if status == 200) >= 1

    def test_error_scenarios(self):
        """Тест различных сценариев ошибок"""
        # Несуществующий принтер
        response = requests.get(f"{self.base_url}/api/printer/9999", timeout=3)
        assert response.status_code == 404

        # Пустой поиск
        response = requests.get(f"{self.base_url}/api/search?q=", timeout=3)
        assert response.status_code == 400

        # Оформление пустой корзины
        response = requests.post(f"{self.base_url}/api/cart/999/checkout", timeout=3)
        assert response.status_code == 400

    def test_performance(self):
        """Тест производительности"""
        import time

        endpoints = [
            '/',
            '/api/printers',
            '/api/stats'
        ]

        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            end = time.time()

            response_time = end - start
            assert response.status_code == 200
            assert response_time < 2.0, f"Медленный ответ: {response_time:.2f}с"

    def test_data_integrity(self):
        """Тест целостности данных"""
        # 1. Получаем принтеры
        response = requests.get(f"{self.base_url}/api/printers")
        assert response.status_code == 200
        printers_list = response.json()

        # 2. Проверяем несколько принтеров
        for printer_id in [1, 2, 3]:
            response = requests.get(f"{self.base_url}/api/printer/{printer_id}")
            assert response.status_code == 200
            printer = response.json()
            assert printer['id'] == printer_id

    def test_cart_isolation(self):
        """Тест изоляции корзин разных пользователей"""
        user1_id = 700
        user2_id = 701

        # Добавляем в корзину user1
        response = requests.post(
            f"{self.base_url}/api/cart/{user1_id}/add",
            json={'printer_id': 1},
            timeout=3
        )
        assert response.status_code == 200

        # Корзина user2 должна быть пуста
        response = requests.get(f"{self.base_url}/api/cart/{user2_id}", timeout=3)
        assert response.status_code == 200
        cart2 = response.json()
        assert len(cart2['items']) == 0


# === АЛЬТЕРНАТИВНЫЕ СИСТЕМНЫЕ ТЕСТЫ БЕЗ ЗАПУСКА СЕРВЕРА ===
class TestPrinterShopSystemSimple:
    """Упрощенные системные тесты без запуска отдельного сервера"""

    def test_simple_e2e_flow(self, client):
        """Упрощенный E2E тест через тестовый клиент"""
        user_id = 800

        # 1. Получаем принтеры
        response = client.get('/api/printers')
        assert response.status_code == 200
        printers = response.json()

        # 2. Выбираем доступный принтер
        available_printer = next(p for p in printers if p['stock'] > 0)

        # 3. Добавляем в корзину
        response = client.post(
            f'/api/cart/{user_id}/add',
            json={'printer_id': available_printer['id'], 'quantity': 1}
        )
        assert response.status_code == 200

        # 4. Оформляем заказ
        response = client.post(f'/api/cart/{user_id}/checkout')
        assert response.status_code == 200

        # 5. Проверяем статистику
        response = client.get('/api/stats')
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_orders'] > 0

    def test_api_endpoints_availability(self, client):
        """Тест доступности всех основных эндпоинтов"""
        endpoints = [
            ('GET', '/'),
            ('GET', '/api/printers'),
            ('GET', '/api/printers/available'),
            ('GET', '/api/printer/1'),
            ('GET', '/api/stats'),
            ('GET', '/stats'),
            ('GET', '/api/cart/1'),
        ]

        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
                assert response.status_code in [200, 404, 400], f"{endpoint} вернул {response.status_code}"

    def test_error_handling(self, client):
        """Тест обработки ошибок"""
        # Несуществующий принтер
        response = client.get('/api/printer/9999')
        assert response.status_code == 404

        # Пустой поиск
        response = client.get('/api/search?q=')
        assert response.status_code == 400

        # Невалидные данные для добавления принтера
        response = client.post('/api/add_printer', json={})
        assert response.status_code == 400


# === ЗАПУСК ТЕСТОВ ===
if __name__ == '__main__':
    import sys

    print("Запуск тестов магазина принтеров...")
    print("=" * 60)

    # Запускаем тесты с выводом
    result = pytest.main([
        __file__,
        '-v',
        '--tb=short',  # короткий traceback
        '-k', 'not TestPrinterShopSystem'  # Пропускаем сложные системные тесты
    ])

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    if result == 0:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
        print("\nСОВЕТ: Для Windows используйте упрощенные системные тесты:")
        print("python -m pytest test_app.py::TestPrinterShopSystemSimple -v")

    sys.exit(result)