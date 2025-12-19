"""
Скрипт для запуска всех тестов магазина принтеров
"""

import subprocess
import sys
import time


def run_tests(test_file, test_name=None):
    """Запустить тесты из файла"""
    print(f"\n{'=' * 70}")
    print(f"🧪 ЗАПУСК: {test_file}")
    print('=' * 70)

    cmd = [sys.executable, '-m', 'pytest', test_file, '-v']
    if test_name:
        cmd.extend(['-k', test_name])

    start_time = time.time()
    result = subprocess.run(cmd)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"\n⏱️  Время выполнения: {execution_time:.2f} секунд")

    return result.returncode, execution_time


def main():
    """Основная функция запуска тестов"""
    print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ МАГАЗИНА ПРИНТЕРОВ")
    print(f"Версия Python: {sys.version.split()[0]}")
    print(f"Платформа: {sys.platform}")

    all_passed = True
    total_time = 0

    # 1. Модульные тесты
    print("\n" + "=" * 70)
    print("1. МОДУЛЬНЫЕ ТЕСТЫ")
    print("=" * 70)
    print("Тестирование классов и бизнес-логики...")

    result, time_taken = run_tests('test_unit.py')
    if result != 0:
        all_passed = False
    total_time += time_taken

    # 2. Интеграционные тесты
    print("\n" + "=" * 70)
    print("2. ИНТЕГРАЦИОННЫЕ ТЕСТЫ")
    print("=" * 70)
    print("Тестирование API эндпоинтов...")

    result, time_taken = run_tests('test_integration.py')
    if result != 0:
        all_passed = False
    total_time += time_taken

    # 3. Системные тесты
    print("\n" + "=" * 70)
    print("3. СИСТЕМНЫЕ ТЕСТЫ (E2E)")
    print("=" * 70)
    print("Тестирование полного процесса покупки...")

    result, time_taken = run_tests('test_system.py')
    if result != 0:
        all_passed = False
    total_time += time_taken

    # Итоги
    print("\n" + "=" * 70)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)

    if all_passed:
        print("✅ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        print(f"   Общее время: {total_time:.2f} секунд")
        print(f"   Всего проверок: ~50+ различных сценариев")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("   Проверьте вывод выше для деталей")

    print("\n📋 ЧТО БЫЛО ПРОТЕСТИРОВАНО:")
    print("   • Модульные тесты: класс Printer, бизнес-логика")
    print("   • Интеграционные тесты: все API эндпоинты")
    print("   • Системные тесты: полный E2E поток покупки")
    print("   • Обработка ошибок: 400, 404 и другие ошибки")
    print("   • Производительность: время отклика API")
    print("   • Согласованность данных")

    print("\n🖨️  Для запуска приложения выполните: python app.py")
    print("🌐 Затем откройте в браузере: http://localhost:5000")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())