from flask import Flask, render_template, jsonify, request
from models import Circus, Performer
import json

app = Flask(__name__)

# Инициализация цирка
circus = Circus("Великий Московский Цирк")

# Добавляем артистов
circus.add_performer(Performer("Иван", "акробат", 8))
circus.add_performer(Performer("Мария", "жонглер", 9))
circus.add_performer(Performer("Петр", "клоун", 7))
circus.add_performer(Performer("Анна", "дрессировщик", 10))


@app.route('/')
def index():
    """Главная страница цирка"""
    return render_template('index.html',
                           circus_name=circus.name,
                           performers=circus.performers,
                           total_performers=len(circus.performers))


@app.route('/api/performers', methods=['GET'])
def get_performers():
    """API для получения списка артистов"""
    performers_data = [
        {
            'id': i,
            'name': p.name,
            'role': p.role,
            'skill_level': p.skill_level,
            'is_available': p.is_available
        }
        for i, p in enumerate(circus.performers)
    ]
    return jsonify({'performers': performers_data})


@app.route('/api/performer/<int:performer_id>', methods=['GET'])
def get_performer(performer_id):
    """API для получения информации об артисте"""
    if performer_id < 0 or performer_id >= len(circus.performers):
        return jsonify({'error': 'Артист не найден'}), 404

    performer = circus.performers[performer_id]
    return jsonify({
        'id': performer_id,
        'name': performer.name,
        'role': performer.role,
        'skill_level': performer.skill_level,
        'is_available': performer.is_available
    })


@app.route('/api/performer/<int:performer_id>/toggle', methods=['POST'])
def toggle_performer(performer_id):
    """Переключение статуса доступности артиста"""
    if performer_id < 0 or performer_id >= len(circus.performers):
        return jsonify({'error': 'Артист не найден'}), 404

    performer = circus.performers[performer_id]
    performer.toggle_availability()

    return jsonify({
        'id': performer_id,
        'name': performer.name,
        'is_available': performer.is_available,
        'message': f'Статус {performer.name} изменен'
    })


@app.route('/api/add_performer', methods=['POST'])
def add_performer():
    """Добавление нового артиста"""
    data = request.get_json()

    if not data or 'name' not in data or 'role' not in data:
        return jsonify({'error': 'Необходимы name и role'}), 400

    name = data['name']
    role = data['role']
    skill_level = data.get('skill_level', 5)

    new_performer = Performer(name, role, skill_level)
    circus.add_performer(new_performer)

    return jsonify({
        'id': len(circus.performers) - 1,
        'name': name,
        'role': role,
        'skill_level': skill_level,
        'message': 'Артист добавлен'
    }), 201


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Статистика цирка"""
    stats = circus.get_stats()
    return jsonify(stats)


@app.route('/performer/<int:performer_id>')
def performer_page(performer_id):
    """Страница артиста"""
    if performer_id < 0 or performer_id >= len(circus.performers):
        return "Артист не найден", 404

    performer = circus.performers[performer_id]
    return render_template('performer.html',
                           performer=performer,
                           performer_id=performer_id,
                           circus_name=circus.name)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)