import pytest
import json
from app import app, products, cart, orders
from models import Product


@pytest.fixture
def client():
    """Фикстура для тестового клиента Flask"""
    app.config['TESTING'] = True

    # Сохраняем исходное состояние
    original_products = products.copy()
    original_cart_items = cart.items.copy()
    original_orders = orders.copy()

    with app.test_client() as client:
        yield client

    # Восстанавливаем исходное состояние после каждого теста
    products.clear()
    products.extend(original_products)

    cart.items.clear()
    cart.items.extend(original_cart_items)

    orders.clear()
    orders.extend(original_orders)


class TestAppIntegration:
    """Интеграционные тесты Flask приложения"""

    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Онлайн магазин' in response.data

    def test_get_products(self, client):
        """Тест получения списка товаров"""
        response = client.get('/api/products')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 5

        # Проверяем структуру первого товара
        first_product = data[0]
        assert 'id' in first_product
        assert 'name' in first_product
        assert 'price' in first_product
        assert 'category' in first_product
        assert 'stock' in first_product

    def test_get_product_by_id(self, client):
        """Тест получения товара по ID"""
        response = client.get('/api/products/1')
        assert response.status_code == 200

        product = response.get_json()
        assert product['id'] == 1
        assert product['name'] == "Ноутбук Dell XPS"

    def test_get_nonexistent_product(self, client):
        """Тест получения несуществующего товара"""
        response = client.get('/api/products/999')
        assert response.status_code == 404

        data = response.get_json()
        assert 'error' in data

    def test_add_new_product(self, client):
        """Тест добавления нового товара"""
        new_product = {
            'name': 'Новый товар',
            'price': 5000,
            'category': 'тест',
            'stock': 10
        }

        response = client.post('/api/products',
                               data=json.dumps(new_product),
                               content_type='application/json')

        assert response.status_code == 201

        data = response.get_json()
        assert data['message'] == 'Товар добавлен'
        assert data['product']['name'] == 'Новый товар'
        assert data['product']['price'] == 5000

        # Проверить, что товар действительно добавился
        response = client.get('/api/products')
        products_list = response.get_json()
        assert len(products_list) == 6

    def test_add_product_invalid_data(self, client):
        """Тест добавления товара с невалидными данными"""
        response = client.post('/api/products',
                               data=json.dumps({'name': 'Только имя'}),
                               content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_get_empty_cart(self, client):
        """Тест получения пустой корзины"""
        response = client.get('/api/cart')
        assert response.status_code == 200

        cart_data = response.get_json()
        assert cart_data['items'] == []
        assert cart_data['total'] == 0
        assert cart_data['item_count'] == 0

    def test_add_to_cart(self, client):
        """Тест добавления товара в корзину"""
        # Добавляем товар в корзину
        response = client.post('/api/cart/add',
                               data=json.dumps({'product_id': 1, 'quantity': 2}),
                               content_type='application/json')

        assert response.status_code == 200

        data = response.get_json()
        assert data['message'] == 'Товар добавлен в корзину'
        assert len(data['cart']['items']) == 1
        assert data['cart']['items'][0]['product_id'] == 1
        assert data['cart']['items'][0]['quantity'] == 2

        # Проверить через GET запрос
        response = client.get('/api/cart')
        cart_data = response.get_json()
        assert cart_data['total'] == 300000  # 150000 * 2

    def test_add_nonexistent_to_cart(self, client):
        """Тест добавления несуществующего товара в корзину"""
        response = client.post('/api/cart/add',
                               data=json.dumps({'product_id': 999}),
                               content_type='application/json')

        assert response.status_code == 404

    def test_add_out_of_stock_to_cart(self, client):
        """Тест добавления отсутствующего товара в корзину"""
        # Товар с ID 3 имеет stock = 5, попробуем добавить 10
        response = client.post('/api/cart/add',
                               data=json.dumps({'product_id': 3, 'quantity': 10}),
                               content_type='application/json')

        assert response.status_code == 400

    def test_remove_from_cart(self, client):
        """Тест удаления товара из корзины"""
        # Сначала добавляем товар
        client.post('/api/cart/add',
                    data=json.dumps({'product_id': 1}),
                    content_type='application/json')

        # Удаляем его
        response = client.post('/api/cart/remove',
                               data=json.dumps({'product_id': 1}),
                               content_type='application/json')

        assert response.status_code == 200

        data = response.get_json()
        assert data['message'] == 'Товар удален из корзины'
        assert data['cart']['items'] == []

    def test_checkout(self, client):
        """Тест оформления заказа"""
        # Добавляем товар в корзину
        client.post('/api/cart/add',
                    data=json.dumps({'product_id': 1, 'quantity': 1}),
                    content_type='application/json')

        # Оформляем заказ
        response = client.post('/api/checkout')
        assert response.status_code == 200

        data = response.get_json()
        assert data['message'] == 'Заказ оформлен'
        assert data['order']['total'] == 150000

        # Проверить, что корзина очистилась
        response = client.get('/api/cart')
        cart_data = response.get_json()
        assert cart_data['items'] == []

        # Проверить, что заказ добавился в список
        response = client.get('/api/orders')
        orders_list = response.get_json()
        assert len(orders_list) == 1

    def test_checkout_empty_cart(self, client):
        """Тест оформления пустой корзины"""
        response = client.post('/api/checkout')
        assert response.status_code == 400

    def test_get_orders(self, client):
        """Тест получения списка заказов"""
        # Создаем заказ
        client.post('/api/cart/add', json={'product_id': 1})
        client.post('/api/checkout')

        response = client.get('/api/orders')
        assert response.status_code == 200

        orders_list = response.get_json()
        assert isinstance(orders_list, list)
        assert len(orders_list) == 1

    def test_get_stats(self, client):
        """Тест получения статистики"""
        # Создаем заказ для статистики
        client.post('/api/cart/add', json={'product_id': 1})
        client.post('/api/checkout')

        response = client.get('/api/stats')
        assert response.status_code == 200

        stats = response.get_json()
        assert 'total_products' in stats
        assert 'total_orders' in stats
        assert 'total_revenue' in stats
        assert 'most_popular_category' in stats
        assert stats['total_orders'] == 1
        assert stats['total_revenue'] == 150000

    def test_html_pages(self, client):
        """Тест HTML страниц"""
        # Страница корзины
        response = client.get('/cart')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

        # Страница заказов
        response = client.get('/orders')
        assert response.status_code == 200

        # Страница статистики
        response = client.get('/stats')
        assert response.status_code == 200

    def test_stock_updates_after_checkout(self, client):
        """Тест обновления запасов после оформления заказа"""
        # Получаем начальный запас
        response = client.get('/api/products/1')
        initial_stock = response.get_json()['stock']

        # Добавляем в корзину и оформляем
        client.post('/api/cart/add', json={'product_id': 1, 'quantity': 2})
        client.post('/api/checkout')

        # Проверяем что запас уменьшился
        response = client.get('/api/products/1')
        final_stock = response.get_json()['stock']

        assert final_stock == initial_stock - 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])