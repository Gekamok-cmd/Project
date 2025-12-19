import pytest
import requests
import time
import subprocess
import os
import sys
import json


class TestStoreSystem:
    """Системные тесты интернет-магазина"""

    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Запуск сервера для системных тестов"""
        self.port = 5001  # Используем другой порт
        self.base_url = f"http://localhost:{self.port}"

        # Запускаем сервер в отдельном процессе
        self.server_process = subprocess.Popen(
            [sys.executable, 'app.py'],
            env={**os.environ, 'FLASK_RUN_PORT': str(self.port)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Ждем запуска сервера (максимум 10 секунд)
        for _ in range(20):
            try:
                response = requests.get(f"{self.base_url}/", timeout=1)
                if response.status_code == 200:
                    break
            except:
                time.sleep(0.5)
        else:
            self.stop_server()
            raise RuntimeError("Сервер не запустился")

        yield

        self.stop_server()

    def stop_server(self):
        """Остановка сервера"""
        if hasattr(self, 'server_process') and self.server_process:
            self.server_process.terminate()
            self.server_process.wait()

    def test_system_availability(self):
        """Тест доступности системы"""
        response = requests.get(f"{self.base_url}/", timeout=5)
        assert response.status_code == 200
        assert 'Онлайн магазин' in response.text

    def test_full_ecommerce_flow(self):
        """Полный E2E тест процесса покупки"""
        # 1. Получить список товаров
        response = requests.get(f"{self.base_url}/api/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 1

        # 2. Выбрать товар
        selected_product = products[0]
        product_id = selected_product['id']
        initial_stock = selected_product['stock']

        # 3. Добавить в корзину
        response = requests.post(
            f"{self.base_url}/api/cart/add",
            json={'product_id': product_id, 'quantity': 1}
        )
        assert response.status_code == 200
        cart_data = response.json()['cart']
        assert len(cart_data['items']) == 1

        # 4. Проверить корзину через API
        response = requests.get(f"{self.base_url}/api/cart")
        assert response.status_code == 200
        cart = response.json()
        assert cart['total'] == selected_product['price']

        # 5. Проверить HTML страницу корзины
        response = requests.get(f"{self.base_url}/cart")
        assert response.status_code == 200
        assert 'Корзина' in response.text

        # 6. Оформить заказ
        response = requests.post(f"{self.base_url}/api/checkout")
        assert response.status_code == 200
        order_data = response.json()
        assert 'order' in order_data
        order_id = order_data['order']['id']

        # 7. Проверить что запас уменьшился
        response = requests.get(f"{self.base_url}/api/products/{product_id}")
        product_after = response.json()
        assert product_after['stock'] == initial_stock - 1

        # 8. Проверить что корзина пуста
        response = requests.get(f"{self.base_url}/api/cart")
        cart_after = response.json()
        assert cart_after['items'] == []

        # 9. Проверить список заказов
        response = requests.get(f"{self.base_url}/api/orders")
        orders = response.json()
        assert len(orders) == 1

        # 10. Проверить конкретный заказ
        response = requests.get(f"{self.base_url}/api/orders")
        orders = response.json()
        assert orders[0]['id'] == order_id

        # 11. Проверить статистику
        response = requests.get(f"{self.base_url}/api/stats")
        stats = response.json()
        assert stats['total_orders'] == 1
        assert stats['total_revenue'] == selected_product['price']

        # 12. Проверить HTML страницу статистики
        response = requests.get(f"{self.base_url}/stats")
        assert response.status_code == 200
        assert 'Статистика' in response.text

    def test_error_handling_system(self):
        """Тест обработки ошибок на системном уровне"""
        # Несуществующий товар
        response = requests.get(f"{self.base_url}/api/products/9999")
        assert response.status_code == 404

        # Невалидный запрос на добавление в корзину
        response = requests.post(f"{self.base_url}/api/cart/add", json={})
        assert response.status_code == 400

        # Оформление пустой корзины
        response = requests.post(f"{self.base_url}/api/checkout")
        assert response.status_code == 400

    def test_performance(self):
        """Тест производительности основных endpoints"""
        import time

        endpoints = [
            '/',
            '/api/products',
            '/api/cart',
            '/api/stats',
            '/cart',
            '/stats'
        ]

        max_response_time = 1.0  # секунд

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < max_response_time, \
                f"{endpoint} отвечает слишком долго: {response_time:.2f}с"

    def test_data_persistence_across_requests(self):
        """Тест сохранения данных между запросами"""
        # 1. Добавить товар в корзину
        response = requests.post(
            f"{self.base_url}/api/cart/add",
            json={'product_id': 1}
        )
        assert response.status_code == 200

        # 2. Проверить в другом запросе
        response = requests.get(f"{self.base_url}/api/cart")
        cart = response.json()
        assert len(cart['items']) == 1

        # 3. Оформить заказ