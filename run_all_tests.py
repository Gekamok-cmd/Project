#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов проекта
"""

import subprocess
import sys
import time


def run_tests(test_file, test_name=None):
    """Запустить тесты"""
    print(f"\n{'=' * 60}")
    print(f"Запуск: {test_file}")
    print('=' * 60)

    cmd = [sys.executable, '-m', 'pytest', test_file, '-v']
    if test_name:
        cmd.extend(['-k', test_name])

    start_time = time.time()
    result = subprocess.run(cmd)
    end_time = time.time()

    print(f"Время выполнения: {end_time - start_time:.2f} секунд")
    return result.returncode


def main():
    """Основная функция"""
    print("🚀 Запуск полного набора тестов")
    print("Версия Python:", sys.version.split()[0])

    all_passed = True

    # 1. Модульные тесты
    if run_tests('test_unit.py') != 0:
        all_passed = False

    # 2. Интеграционные тесты
    if run_tests('test_integration.py') != 0:
        all_passed = False

    # 3. Системные тесты (упрощенные)
    if run_tests('test_system.py', 'TestSystemThroughClient') != 0:
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())