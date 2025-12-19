class Product:
    """Класс товара"""

    def __init__(self, id, name, price, category, stock):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
        self.stock = stock

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'category': self.category,
            'stock': self.stock
        }

    def update_stock(self, quantity):
        """Обновить количество на складе"""
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False


class Cart:
    """Класс корзины"""

    def __init__(self):
        self.items = []  # список товаров в формате {product_id, name, price, quantity}

    def add_item(self, product, quantity=1):
        """Добавить товар в корзину"""
        # Проверяем, есть ли уже такой товар в корзине
        for item in self.items:
            if item['product_id'] == product.id:
                item['quantity'] += quantity
                break
        else:
            self.items.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity
            })

    def remove_item(self, product_id):
        """Удалить товар из корзины"""
        self.items = [item for item in self.items if item['product_id'] != product_id]

    def get_total(self):
        """Получить общую стоимость корзины"""
        return sum(item['price'] * item['quantity'] for item in self.items)

    def clear(self):
        """Очистить корзину"""
        self.items = []

    def to_dict(self):
        return {
            'items': self.items,
            'total': self.get_total(),
            'item_count': len(self.items)
        }


class Order:
    """Класс заказа"""

    def __init__(self, id, items, total):
        self.id = id
        self.items = items  # копия items из корзины
        self.total = total

    def to_dict(self):
        return {
            'id': self.id,
            'items': self.items,
            'total': self.total
        }