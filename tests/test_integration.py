import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Circus, Performer
import json


@pytest.fixture
def client():
    """Фикстура для тестового клиента Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskAppIntegration:
    """Интеграционные тесты Flask приложения"""

    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Великий Московский Цирк' in response.data

    def test_get_performers_api(self, client):
        """Тест API получения артистов"""
        response = client.get('/api/performers')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'performers' in data
        assert len(data['performers']) > 0

        # Проверяем структуру данных
        performer = data['performers'][0]
        assert 'name' in performer
        assert 'role' in performer
        assert 'skill_level' in performer
        assert 'is_available' in performer

    def test_get_single_performer(self, client):
        """Тест API получения одного артиста"""
        response = client.get('/api/performer/0')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'name' in data
        assert 'role' in data
        assert 'skill_level' in data

    def test_get_invalid_performer(self, client):
        """Тест запроса несуществующего артиста"""
        response = client.get('/api/performer/999')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data

    def test_toggle_performer(self, client):
        """Тест переключения статуса артиста"""
        # Сначала получаем текущее состояние
        response = client.get('/api/performer/0')
        initial_data = json.loads(response.data)
        initial_state = initial_data['is_available']

        # Переключаем
        response = client.post('/api/performer/0/toggle')
        assert response.status_code == 200

        toggle_data = json.loads(response.data)
        assert toggle_data['is_available'] != initial_state
        assert 'message' in toggle_data

        # Проверяем, что состояние изменилось
        response = client.get('/api/performer/0')
        final_data = json.loads(response.data)
        assert final_data['is_available'] != initial_state

    def test_add_performer(self, client):
        """Тест добавления нового артиста"""
        new_performer = {
            'name': 'Новый Артист',
            'role': 'фокусник',
            'skill_level': 7
        }

        response = client.post('/api/add_performer',
                               data=json.dumps(new_performer),
                               content_type='application/json')

        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['name'] == 'Новый Артист'
        assert data['role'] == 'фокусник'
        assert data['skill_level'] == 7
        assert 'message' in data

    def test_add_performer_invalid_data(self, client):
        """Тест добавления артиста с невалидными данными"""
        # Отсутствует обязательное поле
        invalid_data = {'name': 'Только имя'}

        response = client.post('/api/add_performer',
                               data=json.dumps(invalid_data),
                               content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_stats(self, client):
        """Тест получения статистики"""
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'total_performers' in data
        assert 'average_skill' in data
        assert 'roles_distribution' in data
        assert 'circus_name' in data

    def test_performer_page(self, client):
        """Тест страницы артиста"""
        response = client.get('/performer/0')
        assert response.status_code == 200
        # Проверяем, что это HTML страница
        assert response.content_type == 'text/html; charset=utf-8'

    def test_performer_page_not_found(self, client):
        """Тест страницы несуществующего артиста"""
        response = client.get('/performer/999')
        assert response.status_code == 404

    def test_api_endpoints_content_type(self, client):
        """Тест Content-Type для API endpoints"""
        endpoints = [
            ('/api/performers', 'GET'),
            ('/api/performer/0', 'GET'),
            ('/api/stats', 'GET'),
        ]

        for endpoint, method in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            assert response.content_type == 'application/json'

    def test_sequential_operations(self, client):
        """Тест последовательных операций"""
        # 1. Получаем начальное количество
        response = client.get('/api/performers')
        initial_count = len(json.loads(response.data)['performers'])

        # 2. Добавляем нового артиста
        new_performer = {
            'name': 'Последовательный Тест',
            'role': 'тестер',
            'skill_level': 5
        }
