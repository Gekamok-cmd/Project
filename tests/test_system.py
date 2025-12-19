import pytest
import requests
import time
import subprocess
import os
import signal
from threading import Thread


class TestCircusSystem:
    """Системные тесты (End-to-End) для приложения Цирк"""

    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Запуск и остановка сервера для системных тестов"""
        # Определяем порт для тестов
        self.base_url = "http://localhost:5001"

        # Запускаем сервер в отдельном процессе
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'

        self.server_process = subprocess.Popen(
            ['flask', 'run', '--port', '5001'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # Ждем запуска сервера
        time.sleep(3)

        yield

        # Останавливаем сервер
        os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
        self.server_process.wait()

    def wait_for_server(self, max_attempts=10):
        """Ожидание доступности сервера"""
        for _ in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/api/stats", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.ConnectionError:
                time.sleep(0.5)
        return False

    def test_system_availability(self):
        """Тест доступности всей системы"""
        assert self.wait_for_server(), "Сервер не запустился"

        response = requests.get(self.base_url, timeout=5)
        assert response.status_code == 200
        assert "Великий Московский Цирк" in response.text

    def test_full_user_journey(self):
        """Полный сценарий использования системы пользователем"""
        # 1. Пользователь заходит на главную страницу
        response = requests.get(self.base_url)
        assert response.status_code == 200
        assert "Добро пожаловать" in response.text

        # 2. Пользователь просматривает список артистов через API
        response = requests.get(f"{self.base_url}/api/performers")
        assert response.status_code == 200
        performers = response.json()['performers']
        assert len(performers) > 0

        # 3. Пользователь получает статистику
        response = requests.get(f"{self.base_url}/api/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_performers'] == len(performers)

        # 4. Пользователь переходит на страницу конкретного артиста
        performer_id = performers[0]['id']
        response = requests.get(f"{self.base_url}/performer/{performer_id}")
        assert response.status_code == 200
        assert performers[0]['name'] in response.text

        # 5. Пользователь изменяет статус артиста
        initial_status = performers[0]['is_available']
        response = requests.post(f"{self.base_url}/api/performer/{performer_id}/toggle")
        assert response.status_code == 200
        toggled_data = response.json()
        assert toggled_data['is_available'] != initial_status

        # 6. Пользователь добавляет нового артиста
        new_performer = {
            'name': 'Системный Тест',
            'role': 'системный инженер',
            'skill_level': 10
        }

        response = requests.post(
            f"{self.base_url}/api/add_performer",
            json=new_performer
        )
        assert response.status_code == 201

        # 7. Проверяем, что артист добавился
        response = requests.get(f"{self.base_url}/api/performers")
        updated_performers = response.json()['performers']
        assert len(updated_performers) == len(performers) + 1

        # Ищем добавленного артиста
        added = next((p for p in updated_performers if p['name'] == 'Системный Тест'), None)
        assert added is not None
        assert added['role'] == 'системный инженер'

    def test_concurrent_requests(self):
        """Тест конкурентных запросов"""
        import concurrent.futures

        def make_request(url):
            response = requests.get(url, timeout=5)
            return response.status_code

        urls = [
                   f"{self.base_url}/",
                   f"{self.base_url}/api/performers",
                   f"{self.base_url}/api/stats",
                   f"{self.base_url}/performer/0",
                   f"{self.base_url}/api/performer/0"
               ] * 3  # 15 запросов

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Все запросы должны вернуть 200
        assert all(status == 200 for status in results)

    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Несуществующий артист
        response = requests.get(f"{self.base_url}/api/performer/9999")
        assert response.status_code == 404

        # Неправильный метод
        response = requests.post(f"{self.base_url}/", json={})
        # Flask возвращает 405 для неправильного метода
        assert response.status_code in [405, 404]

        # Неправильные данные для добавления артиста
        response = requests.post(
            f"{self.base_url}/api/add_performer",
            json={'wrong': 'data'}
        )
        assert response.status_code == 400

    def test_performance(self):
        """Тест производительности"""
        import time

        # Тестируем время отклика основных endpoints
        endpoints = [
            '/',
            '/api/performers',
            '/api/stats',
            '/api/performer/0'
        ]

        max_response_time = 1.0  # секунд

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}")
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < max_response_time, \
                f"{endpoint} отвечает слишком долго: {response_time:.2f}с"

    def test_data_persistence(self):
        """Тест сохранения состояния между запросами"""
        # 1. Получаем начальное состояние
        response1 = requests.get(f"{self.base_url}/api/performers")
        initial_count = len(response1.json()['performers'])

        # 2. Добавляем артиста
        new_performer = {
            'name': 'Персистентный',
            'role': 'тестер',
            'skill_level': 8
        }

        requests.post(f"{self.base_url}/api/add_performer", json=new_performer)

        # 3. Проверяем, что артист добавился
        response2 = requests.get(f"{self.base_url}/api/performers")
        new_count = len(response2.json()['performers'])

        assert new_count == initial_count + 1

    def test_cross_browser_compatibility(self):
        """Тест заголовков и кодировки"""
        response = requests.get(self.base_url)

        # Проверяем важные заголовки
        assert 'text/html' in response.headers['Content-Type']
        assert 'utf-8' in response.headers['Content-Type'].lower()

        # Проверяем кодировку в контенте
        assert '<meta charset="UTF-8">' in response.text

    def test_security_headers(self):
        """Тест security headers"""
        response = requests.get(self.base_url)

        # Проверяем наличие некоторых security headers
        headers = response.headers

        # Flask по умолчанию не устанавливает все security headers,
        # но мы можем проверить базовые
        assert 'Server' in headers  # Проверяем, что сервер идентифицирует себя

        # Проверяем, что нет опасных headers
        assert 'X-Powered-By' not in headers or 'PHP' not in headers['X-Powered-By']


class TestDockerDeployment:
    """Тесты Docker развертывания"""

    def test_docker_build(self):
        """Тест сборки Docker образа"""
        # Проверяем наличие Dockerfile
        assert os.path.exists('Dockerfile'), "Dockerfile не найден"

        # Проверяем содержимое Dockerfile
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()

        assert 'FROM python' in dockerfile_content
        assert 'COPY requirements.txt' in dockerfile_content
        assert 'RUN pip install' in dockerfile_content
        assert 'CMD' in dockerfile_content or 'ENTRYPOINT' in dockerfile_content

    def test_requirements_file(self):
        """Тест файла зависимостей"""
        assert os.path.exists('requirements.txt'), "requirements.txt не найден"

        with open('requirements.txt', 'r') as f:
            requirements = f.read()

        # Проверяем основные зависимости
        assert 'Flask' in requirements
        assert 'pytest' in requirements
        assert 'gunicorn' in requirements


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])