import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Performer, Circus


class TestPerformer:
    """Модульные тесты для класса Performer"""

    def test_performer_creation(self):
        """Тест создания артиста"""
        performer = Performer("Иван", "акробат", 8)
        assert performer.name == "Иван"
        assert performer.role == "акробат"
        assert performer.skill_level == 8
        assert performer.is_available == True

    def test_perform_success(self):
        """Тест успешного выступления"""
        performer = Performer("Мария", "жонглер", 9)
        result = performer.perform()
        assert performer.name in result
        assert performer.role in result

    def test_perform_unavailable(self):
        """Тест выступления недоступного артиста"""
        performer = Performer("Петр", "клоун", 7)
        performer.is_available = False
        result = performer.perform()
        assert "не доступен" in result

    def test_train(self):
        """Тест тренировки артиста"""
        performer = Performer("Анна", "дрессировщик", 5)
        result = performer.train()
        assert performer.skill_level == 6
        assert "повысил навык" in result

    def test_train_max_skill(self):
        """Тест тренировки с максимальным уровнем"""
        performer = Performer("Профи", "мастер", 10)
        performer.train()
        assert performer.skill_level == 10

    def test_toggle_availability(self):
        """Тест переключения доступности"""
        performer = Performer("Тест", "роль", 5)
        initial_state = performer.is_available

        # Первое переключение
        new_state = performer.toggle_availability()
        assert performer.is_available != initial_state
        assert new_state == performer.is_available

        # Второе переключение (возврат)
        performer.toggle_availability()
        assert performer.is_available == initial_state


class TestCircus:
    """Модульные тесты для класса Circus"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.circus = Circus("Тестовый цирк")
        self.performer1 = Performer("Артист1", "акробат", 8)
        self.performer2 = Performer("Артист2", "клоун", 6)
        self.performer3 = Performer("Артист3", "жонглер", 9)

    def test_circus_creation(self):
        """Тест создания цирка"""
        assert self.circus.name == "Тестовый цирк"
        assert len(self.circus.performers) == 0

    def test_add_performer(self):
        """Тест добавления артиста"""
        self.circus.add_performer(self.performer1)
        assert len(self.circus.performers) == 1
        assert self.circus.performers[0] == self.performer1

    def test_remove_performer(self):
        """Тест удаления артиста"""
        self.circus.add_performer(self.performer1)
        self.circus.add_performer(self.performer2)

        removed = self.circus.remove_performer(0)
        assert removed == self.performer1
        assert len(self.circus.performers) == 1
        assert self.circus.performers[0] == self.performer2

    def test_remove_invalid_performer(self):
        """Тест удаления несуществующего артиста"""
        result = self.circus.remove_performer(999)
        assert result is None

    def test_get_best_performers(self):
        """Тест получения лучших артистов"""
        self.circus.add_performer(self.performer1)  # skill 8
        self.circus.add_performer(self.performer2)  # skill 6
        self.circus.add_performer(self.performer3)  # skill 9

        best = self.circus.get_best_performers(min_skill=8)
        assert len(best) == 2
        assert self.performer1 in best
        assert self.performer3 in best
        assert self.performer2 not in best

    def test_get_stats(self):
        """Тест получения статистики"""
        self.circus.add_performer(self.performer1)
        self.circus.add_performer(self.performer2)

        stats = self.circus.get_stats()

        assert stats['total_performers'] == 2
        assert stats['available_performers'] == 2
        assert stats['average_skill'] == 7.0
        assert stats['roles_distribution'] == {'акробат': 1, 'клоун': 1}
        assert stats['circus_name'] == "Тестовый цирк"

    def test_perform_show(self):
        """Тест проведения шоу"""
        self.circus.add_performer(self.performer1)
        self.circus.add_performer(self.performer2)

        show = self.circus.perform_show()

        assert show['show_name'] == 'Шоу Тестовый цирк'
        assert len(show['performances']) == 2
        assert show['total_performers'] == 2

    def test_perform_show_no_available(self):
        """Тест шоу без доступных артистов"""
        self.performer1.is_available = False
        self.performer2.is_available = False
        self.circus.add_performer(self.performer1)
        self.circus.add_performer(self.performer2)

        result = self.circus.perform_show()
        assert result == "Нет доступных артистов для шоу"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])