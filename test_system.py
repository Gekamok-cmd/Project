"""
Системные тесты магазина принтеров
"""

import pytest


class TestSystemThroughClient:
    """Системные тесты через тестовый клиент Flask"""

    @pytest.fixture
    def client(self):
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Очищаем корзины и заказы перед каждым тестом
            from app import carts, orders
            carts.clear()
            orders.clear()
            yield client

    def test_full_e2e_shopping_flow(self, client):
        """Полный E2E тест процесса покупки"""
        print("\n=== Начало E2E теста процесса покупки ===")

        # 1. Пользователь заходит на главную страницу
        response = client.get('/')
        assert response.status_code == 200
        print("✅ Главная страница загружена")

        # 2. Просматривает все принтеры
        response = client.get('/api/printers')
        assert response.status_code == 200
        printers = response.get_json()
        assert len(printers) > 0
        print(f"✅ Получено {len(printers)} принтеров")

        # 3. Ищет принтер по бренду
        response = client.get('/api/search?q=canon')
        assert response.status_code == 200
        canon_printers = response.get_json()
        assert len(canon_printers) > 0
        print(f"✅ Найдено {len(canon_printers)} принтеров Canon")

        # 4. Смотрит только принтеры в наличии
        response = client.get('/api/printers/available')
        assert response.status_code == 200
        available_printers = response.get_json()
        assert len(available_printers) > 0
        print(f"✅ В наличии {len(available_printers)} принтеров")

        # 5. Выбирает конкретный принтер
        selected_printer = available_printers[0]
        printer_id = selected_printer['id']
        printer_name = selected_printer['name']
        printer_price = selected_printer['price']

        print(f"✅ Выбран принтер: {printer_name} за {printer_price} руб.")

        # 6. Добавляет в корзину
        user_id = 12345
        response = client.post('/api/cart/add',
                               json={
                                   'user_id': user_id,
                                   'printer_id': printer_id,
                                   'quantity': 1
                               })
        assert response.status_code == 200
        print("✅ Принтер добавлен в корзину")

        # 7. Проверяет корзину
        response = client.get(f'/api/cart/{user_id}')
        assert response.status_code == 200
        cart = response.get_json()
        assert len(cart['items']) == 1
        assert cart['total'] == printer_price
        print(f"✅ Корзина проверена: {cart['total']} руб.")

        # 8. Оформляет заказ
        response = client.post('/api/checkout',
                               json={'user_id': user_id})
        assert response.status_code == 200
        order = response.get_json()['order']
        print(f"✅ Заказ оформлен: #{order['order_id']} на {order['total']} руб.")

        # 9. Проверяет, что корзина пуста
        response = client.get(f'/api/cart/{user_id}')
        cart = response.get_json()
        assert cart['items'] == []
        print("✅ Корзина очищена после заказа")

        # 10. Проверяет список заказов
        response = client.get('/api/orders')
        orders_list = response.get_json()
        assert len(orders_list) == 1
        print("✅ Заказ сохранен в системе")

        # 11. Проверяет статистику магазина
        response = client.get('/api/stats')
        stats = response.get_json()
        assert stats['total_orders'] == 1
        assert stats['total_revenue'] == printer_price
        print("✅ Статистика обновлена")

        # 12. Получает детали заказа
        order_id = orders_list[0]['order_id']
        response = client.get(f'/api/orders/{order_id}')
        assert response.status_code == 200
        order_details = response.get_json()
        assert order_details['order_id'] == order_id
        print(f"✅ Детали заказа #{order_id} получены")

        print("=== E2E тест успешно завершен ===")

    def test_multiple_users_shopping(self, client):
        """Тест покупок несколькими пользователями"""
        print("\n=== Тест нескольких пользователей ===")

        # Пользователь 1
        response = client.post('/api/cart/add',
                               json={'user_id': 1, 'printer_id': 1, 'quantity': 1})
        assert response.status_code == 200

        # Пользователь 2
        response = client.post('/api/cart/add',
                               json={'user_id': 2, 'printer_id': 2, 'quantity': 2})
        assert response.status_code == 200

        # Проверяем корзину пользователя 1
        response = client.get('/api/cart/1')
        cart1 = response.get_json()
        assert len(cart1['items']) == 1
        assert cart1['items'][0]['printer_id'] == 1

        # Проверяем корзину пользователя 2
        response = client.get('/api/cart/2')
        cart2 = response.get_json()
        assert len(cart2['items']) == 1
        assert cart2['items'][0]['printer_id'] == 2
        assert cart2['items'][0]['quantity'] == 2

        print("✅ Корзины пользователей изолированы")

    def test_error_scenarios(self, client):
        """Тест различных сценариев ошибок"""
        print("\n=== Тест обработки ошибок ===")

        # 1. Несуществующий принтер
        response = client.get('/api/printers/9999')
        assert response.status_code == 404
        print("✅ Ошибка 404 для несуществующего принтера")

        # 2. Невалидный тип принтера
        response = client.get('/api/printers/type/invalid_type')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0  # Пустой список для невалидного типа
        print("✅ Пустой список для невалидного типа принтера")

        # 3. Пустой поисковой запрос
        response = client.get('/api/search?q=')
        assert response.status_code == 400
        print("✅ Ошибка 400 для пустого поиска")

        # 4. Оформление пустой корзины
        response = client.post('/api/checkout',
                               json={'user_id': 999})
        assert response.status_code == 400
        print("✅ Ошибка 400 для пустой корзины")

        # 5. Невалидные данные для добавления в корзину
        response = client.post('/api/cart/add',
                               json={'user_id': 1})  # Нет printer_id
        assert response.status_code == 400
        print("✅ Ошибка 400 для невалидных данных корзины")

        # 6. Добавление отсутствующего товара
        response = client.post('/api/cart/add',
                               json={'user_id': 1, 'printer_id': 4, 'quantity': 1})
        assert response.status_code == 400
        print("✅ Ошибка 400 для отсутствующего товара")

        print("=== Все сценарии ошибок обработаны корректно ===")

    def test_performance_endpoints(self, client):
        """Тест производительности основных эндпоинтов"""
        print("\n=== Тест производительности ===")

        import time

        endpoints = [
            ('/', 'Главная страница'),
            ('/api/printers', 'Все принтеры'),
            ('/api/printers/available', 'Принтеры в наличии'),
            ('/api/stats', 'Статистика'),
        ]

        max_response_time = 1.0  # секунд

        for endpoint, description in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < max_response_time, \
                f"{description} отвечает слишком долго: {response_time:.2f}с"

            print(f"✅ {description}: {response_time:.3f} сек")

        print("=== Все эндпоинты отвечают быстро ===")

    def test_data_consistency(self, client):
        """Тест согласованности данных"""
        print("\n=== Тест согласованности данных ===")

        # 1. Получаем все принтеры
        response = client.get('/api/printers')
        all_printers = response.get_json()

        # 2. Проверяем каждого принтера по отдельности
        for printer in all_printers[:3]:  # Проверяем первые 3
            printer_id = printer['id']
            response = client.get(f'/api/printers/{printer_id}')
            single_printer = response.get_json()

            # Данные должны совпадать
            assert single_printer['id'] == printer['id']
            assert single_printer['name'] == printer['name']
            assert single_printer['price'] == printer['price']

        print("✅ Данные согласованы между общим списком и отдельными эндпоинтами")

        # 3. Проверяем статистику
        response = client.get('/api/stats')
        stats = response.get_json()

        assert stats['total_printers'] == len(all_printers)
        print(f"✅ Статистика корректна: {stats['total_printers']} принтеров")

        print("=== Тест согласованности данных пройден ===")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])