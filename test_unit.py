"""
Модульные тесты для магазина принтеров
"""

import pytest

# Импортируем класс Printer из app.py
from app import Printer


class TestPrinter:
    """Тесты класса Printer"""

    def test_printer_creation(self):
        """Тест создания принтера"""
        printer = Printer(
            id=1,
            name="Test Printer",
            printer_type="laser",
            price=10000,
            color=True,
            speed=25,
            stock=5
        )

        assert printer.id == 1
        assert printer.name == "Test Printer"
        assert printer.type == "laser"
        assert printer.price == 10000
        assert printer.color == True
        assert printer.speed == 25
        assert printer.stock == 5

    def test_printer_to_dict(self):
        """Тест преобразования в словарь"""
        printer = Printer(2, "Printer 2", "inkjet", 8000, False, 15, 3)
        printer_dict = printer.to_dict()

        assert isinstance(printer_dict, dict)
        assert printer_dict['id'] == 2
        assert printer_dict['name'] == "Printer 2"
        assert printer_dict['type'] == "inkjet"
        assert printer_dict['price'] == 8000
        assert printer_dict['color'] == False
        assert printer_dict['speed'] == 15
        assert printer_dict['stock'] == 3

    def test_printer_types_validation(self):
        """Тест допустимых типов принтеров"""
        valid_types = ['laser', 'inkjet', 'multifunctional']

        for printer_type in valid_types:
            printer = Printer(1, "Test", printer_type, 10000, True, 20, 5)
            assert printer.type == printer_type

    def test_printer_comparison(self):
        """Тест сравнения принтеров"""
        printer1 = Printer(1, "Printer A", "laser", 10000, True, 20, 5)
        printer2 = Printer(2, "Printer B", "inkjet", 8000, False, 15, 3)

        assert printer1.id != printer2.id
        assert printer1.price > printer2.price
        assert printer1.color != printer2.color


class TestBusinessLogic:
    """Тесты бизнес-логики"""

    def test_calculate_total_price(self):
        """Тест расчета общей стоимости"""
        # Мокаем данные корзины
        cart_items = [
            {'printer_id': 1, 'name': 'Printer 1', 'price': 10000, 'quantity': 2},
            {'printer_id': 2, 'name': 'Printer 2', 'price': 8000, 'quantity': 1}
        ]

        total = sum(item['price'] * item['quantity'] for item in cart_items)
        assert total == 28000  # 10000*2 + 8000

    def test_stock_availability(self):
        """Тест проверки наличия товара"""
        printers = [
            Printer(1, "Printer 1", "laser", 10000, True, 20, 5),  # в наличии
            Printer(2, "Printer 2", "inkjet", 8000, False, 15, 0),  # нет в наличии
        ]

        available = [p for p in printers if p.stock > 0]
        out_of_stock = [p for p in printers if p.stock == 0]

        assert len(available) == 1
        assert len(out_of_stock) == 1
        assert available[0].id == 1
        assert out_of_stock[0].id == 2

    def test_filter_by_type(self):
        """Тест фильтрации по типу"""
        printers = [
            Printer(1, "Laser 1", "laser", 10000, True, 20, 5),
            Printer(2, "Laser 2", "laser", 15000, False, 25, 3),
            Printer(3, "Inkjet 1", "inkjet", 8000, True, 15, 8),
        ]

        laser_printers = [p for p in printers if p.type == "laser"]
        inkjet_printers = [p for p in printers if p.type == "inkjet"]

        assert len(laser_printers) == 2
        assert len(inkjet_printers) == 1
        assert all(p.type == "laser" for p in laser_printers)
        assert all(p.type == "inkjet" for p in inkjet_printers)

    def test_search_functionality(self):
        """Тест поиска"""
        printers = [
            Printer(1, "HP LaserJet Pro", "laser", 25000, False, 40, 5),
            Printer(2, "Canon PIXMA", "inkjet", 12000, True, 15, 3),
            Printer(3, "Epson WorkForce", "multifunctional", 30000, True, 25, 2),
        ]

        # Поиск по части названия
        search_query = "hp"
        results = [p for p in printers if search_query in p.name.lower()]

        assert len(results) == 1
        assert "HP" in results[0].name

        # Поиск по другому запросу
        search_query = "pro"
        results = [p for p in printers if search_query in p.name.lower()]
        assert len(results) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])