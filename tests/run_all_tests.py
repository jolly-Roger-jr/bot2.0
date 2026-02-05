# tests/run_all_tests.py
import sys
import os
import subprocess

print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ ИЗ tests/ ДИРЕКТОРИИ")
print("=" * 50)


def run_test(test_file):
    """Запуск отдельного теста"""
    print(f"\n▶️ Запуск: {test_file}")
    print("-" * 40)

    try:
        # Запускаем тест как модуль
        result = subprocess.run(
            [sys.executable, "-m", f"tests.{test_file.replace('.py', '')}"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Ошибка запуска теста: {e}")
        return False


def main():
    """Основная функция запуска тестов"""
    test_files = [
        "check_imports",
        "test_keyboards",
        "test_integration"
    ]

    results = []

    for test_file in test_files:
        success = run_test(test_file)
        results.append((test_file, success))
        print(f"\n{'=' * 50}\n")

    # Итоговый отчет
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ВСЕМ ТЕСТАМ:")
    print("=" * 50)

    for test_file, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{status} - {test_file}")

    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"📈 ИТОГО: {passed}/{total} тестов пройдено ({passed / total * 100:.0f}%)")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
    