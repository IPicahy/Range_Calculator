"""
Баллистический калькулятор MOA для игр/стрельбы
Поддержка профилей, подтверждённых точек, интерполяция и генерация таблиц.
"""

import json
import os
import numpy as np
import sys

PROFILES_FILE = "ballistic_profiles.json"


# ======================== РАБОТА С ФАЙЛАМИ ========================
def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_profiles(profiles):
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)


# ======================== МАТЕМАТИКА ========================
def interpolate_moa(points, target_dist):
    """Кусочно-линейная интерполяция по подтверждённым точкам (самый надёжный метод для игр)"""
    if len(points) < 2:
        return None, "Недостаточно точек для расчёта (минимум 2)"

    # Сортируем по дистанции
    pts = sorted(points, key=lambda p: p[0])
    x = [p[0] for p in pts]
    y = [p[1] for p in pts]

    # Внутри диапазона -> линейная интерполяция
    if x[0] <= target_dist <= x[-1]:
        return float(np.interp(target_dist, x, y)), None

    # За пределами -> экстраполяция по последнему сегменту (с предупреждением)
    warn = "⚠️ Дистанция вне подтверждённого диапазона. Значение экстраполировано."
    if target_dist < x[0]:
        dx = x[1] - x[0]
        dy = y[1] - y[0]
        return y[0] - (dy / dx) * (x[0] - target_dist), warn
    else:
        dx = x[-1] - x[-2]
        dy = y[-1] - y[-2]
        return y[-1] + (dy / dx) * (target_dist - x[-1]), warn


def generate_table(points, start=100, end=1500, step=50):
    """Генерирует таблицу MOA с заданным шагом"""
    table = []
    for d in range(start, end + step, step):
        moa, _ = interpolate_moa(points, d)
        if moa is not None:
            table.append((d, round(moa, 2)))
    return table


# ======================== ИНТЕРФЕЙС ========================
def print_header(text):
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def main():
    profiles = load_profiles()

    # Создаём дефолтный профиль при первом запуске
    if not profiles:
        profiles[".338 LM (Default)"] = {
            "points": [
                [100, 0.8], [200, 3.2], [300, 6.8], [400, 8.0],
                [450, 9.5], [466, 10.0], [500, 11.0], [550, 13.3],
                [600, 15.5], [650, 17.8], [700, 20.0], [750, 22.4],
                [800, 24.9], [850, 27.6], [900, 30.6], [950, 33.8],
                [1000, 37.1], [1050, 40.6], [1100, 44.4], [1150, 48.4],
                [1200, 52.5], [1250, 56.9], [1300, 61.4], [1350, 66.2],
                [1400, 71.1], [1450, 76.2], [1500, 81.6]
            ],
            "desc": "Бронебойный .338 LM, якорь 700м=20.0 MOA"
        }
        save_profiles(profiles)

    while True:
        print_header("🎯 БАЛЛИСТИЧЕСКИЙ КАЛЬКУЛЯТОР MOA")
        print("1. Выбрать/создать профиль")
        print("2. Добавить/изменить подтверждённую точку")
        print("3. Удалить точку")
        print("4. Рассчитать MOA для дистанции")
        print("5. Сгенерировать таблицу (100-1500 м)")
        print("6. Сохранить и выйти")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            print("\n📁 Доступные профили:")
            for i, name in enumerate(profiles, 1):
                print(f"  {i}. {name}")
            sel = input("Номер профиля или название нового: ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(profiles):
                    current_name = list(profiles.keys())[idx]
                else:
                    print("❌ Неверный номер")
                    continue
            else:
                if sel not in profiles:
                    profiles[sel] = {"points": [], "desc": input("Описание профиля: ")}
                current_name = sel
            print(f"✅ Выбран профиль: {current_name}")
            input("Нажмите Enter для возврата...")

        elif choice == "2":
            if 'current_name' not in locals():
                print("⚠️ Сначала выберите профиль (пункт 1)")
                input("Нажмите Enter...");
                continue
            dist = float(input("Дистанция (м): "))
            moa = float(input("MOA: "))
            pts = profiles[current_name]["points"]
            # Заменяем или добавляем
            for i, p in enumerate(pts):
                if p[0] == dist:
                    pts[i][1] = moa
                    print(f"📝 Точка {dist} м обновлена на {moa} MOA")
                    break
            else:
                pts.append([dist, moa])
                pts.sort(key=lambda x: x[0])
                print(f"➕ Добавлена точка: {dist} м = {moa} MOA")
            profiles[current_name]["points"] = pts
            input("Нажмите Enter...")

        elif choice == "3":
            if 'current_name' not in locals():
                print("⚠️ Сначала выберите профиль (пункт 1)")
                input("Нажмите Enter...");
                continue
            pts = profiles[current_name]["points"]
            if not pts: print("📭 Точек нет"); input("Enter..."); continue
            print("\nТочки профиля:")
            for p in pts: print(f"  {p[0]} м -> {p[1]} MOA")
            rem = float(input("Удалить точку (введите дистанцию): "))
            profiles[current_name]["points"] = [p for p in pts if p[0] != rem]
            print("🗑️ Точка удалена")
            input("Enter...")

        elif choice == "4":
            if 'current_name' not in locals():
                print("⚠️ Сначала выберите профиль (пункт 1)")
                input("Enter...");
                continue
            dist = float(input("\n🎯 Введите дистанцию до цели (м): "))
            pts = profiles[current_name]["points"]
            moa, warn = interpolate_moa(pts, dist)
            if moa is not None:
                print(f"✅ Для {dist} м требуется: {moa:.2f} MOA")
                if warn: print(warn)
            else:
                print("❌ Недостаточно данных")
            input("Enter...")

        elif choice == "5":
            if 'current_name' not in locals():
                print("⚠️ Сначала выберите профиль (пункт 1)")
                input("Enter...");
                continue
            pts = profiles[current_name]["points"]
            table = generate_table(pts)
            print("\n📊 ТАБЛИЦА MOA (шаг 50 м)")
            print("-" * 25)
            for d, m in table:
                mark = "⭐" if any(abs(p[0] - d) < 1 for p in pts) else " "
                print(f"{d:>4} м | {m:>5.2f} MOA {mark}")
            print("-" * 25)
            input("Enter...")

        elif choice == "6":
            save_profiles(profiles)
            print("💾 Профили сохранены. До свидания!")
            sys.exit()
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    main()