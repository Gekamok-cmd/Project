import pytest
from models import Product, Cart, Order


class TestProduct:
    """Модульные тесты для класса Product"""

    def test_product_creation(self):
        """Тест создания товара"""
        product = Product(1, "Тестовый товар", 1000, "категория", 10)

        assert product.id == 1
        assert product.name == "Тестовый товар"
        assert product.price == 1000
        assert product.category == "категория"
        assert product.stock == 10

    def test_product_to_dict(self):
        """Тест преобразования товара в словарь"""
        product = Product(2, "Товар", 500, "тест", 5)
        product_dict = product.to_dict()

        assert product_dict['id'] == 2
        assert product_dict['name'] == "Товар"
        assert product_dict['price'] == 500
        assert product_dict['category'] == "тест"
        assert product_dict['stock'] == 5

    def test_update_stock_success(self):
        """Тест успешного обновления запасов"""
        product = Product(1, "Товар", 100, "кат", 10)

        result = product.update_stock(3)
        assert result == True
        assert product.stock == 7

    def test_update_stock_failure(self):
        """Тест неудачного обновления запасов"""
        product = Product(1, "Товар", 100, "кат", 2)

        result = product.update_stock(5)
        assert result == False
        assert product.stock == 2  # Не изменилось


class TestCart:
    """Модульные тесты для класса Cart"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.cart = Cart()
        self.product1 = Product(1, "Товар 1", 100, "кат1", 10)
        self.product2 = Product(2, "Товар 2", 200, "кат2", 5)

    def test_empty_cart(self):
        """Тест пустой корзины"""
        assert len(self.cart.items) == 0
        assert self.cart.get_total() == 0
        assert self.cart.to_dict()['item_count'] == 0

    def test_add_item(self):
        """Тест добавления товара в корзину"""
        self.cart.add_item(self.product1)

        assert len(self.cart.items) == 1
        assert self.cart.items[0]['product_id'] == 1
        assert self.cart.items[0]['quantity'] == 1
        assert self.cart.get_total() == 100

    def test_add_item_with_quantity(self):
        """Тест добавления товара с количеством"""
        self.cart.add_item(self.product1, 3)

        assert self.cart.items[0]['quantity'] == 3
        assert self.cart.get_total() == 300

    def test_add_multiple_items(self):
        """Тест добавления нескольких товаров"""
        self.cart.add_item(self.product1)
        self.cart.add_item(self.product2)

        assert len(self.cart.items) == 2
        assert self.cart.get_total() == 300

    def test_add_same_item_twice(self):
        """Тест добавления одного товара дважды"""
        self.cart.add_item(self.product1)
        self.cart.add_item(self.product1, 2)

        assert len(self.cart.items) == 1
        assert self.cart.items[0]['quantity'] == 3
        assert self.cart.get_total() == 300

    def test_remove_item(self):
        """Тест удаления товара из корзины"""
        self.cart.add_item(self.product1)
        self.cart.add_item(self.product2)

        self.cart.remove_item(1)

        assert len(self.cart.items) == 1
        assert self.cart.items[0]['product_id'] == 2
        assert self.cart.get_total() == 200

    def test_remove_nonexistent_item(self):
        """Тест удаления несуществующего товара"""
        self.cart.add_item(self.product1)

        # Удаление несуществующего товара не должно вызывать ошибку
        self.cart.remove_item(999)

        assert len(self.cart.items) == 1
        assert self.cart.get_total() == 100

    def test_clear_cart(self):
        """Тест очистки корзины"""
        self.cart.add_item(self.product1)
        self.cart.add_item(self.product2)

        self.cart.clear()

        assert len(self.cart.items) == 0
        assert self.cart.get_total() == 0

    def test_cart_to_dict(self):
        """Тест преобразования корзины в словарь"""
        self.cart.add_item(self.product1, 2)
        cart_dict = self.cart.to_dict()

        assert 'items' in cart_dict
        assert 'total' in cart_dict
        assert 'item_count' in cart_dict
        assert cart_dict['total'] == 200
        assert cart_dict['item_count'] == 1


class TestOrder:
    """Модульные тесты для класса Order"""

    def test_order_creation(self):
        """Тест создания заказа"""
        items = [
            {'product_id': 1, 'name': 'Товар 1', 'price': 100, 'quantity': 2},
            {'product_id': 2, 'name': 'Товар 2', 'price': 200, 'quantity': 1}
        ]

        order = Order(1, items, 400)

        assert order.id == 1
        assert len(order.items) == 2
        assert order.total == 400

    def test_order_to_dict(self):
        """Тест преобразования заказа в словарь"""
        items = [{'product_id': 1, 'name': 'Товар', 'price': 100, 'quantity': 1}]
        order = Order(5, items, 100)
        order_dict = order.to_dict()

        assert order_dict['id'] == 5
        assert order_dict['items'] == items
        assert order_dict['total'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])