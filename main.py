#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D


# Чтение начальных условий из файла
def read_initial_conditions(filename):
    bodies = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                parts = line.split()
                name = parts[0]
                gm = float(parts[1])  #Гравитационный параметр (G × масса тела) в единицах [au³/days²]
                x, y, z = map(float, parts[2:5])  # Гелиоцентрические координаты в астрономических единицах (au)
                vx, vy, vz = map(float, parts[5:8])  #Скорости в [au/day]
                bodies.append({
                    'name': name,
                    'GM': gm,
                    'position': np.array([x, y, z]),
                    'velocity': np.array([vx, vy, vz]),
                    'trajectory': []
                })
    return bodies


# Вычисление ускорений для всех тел
def compute_accelerations(bodies):
    n = len(bodies)
    accelerations = [np.zeros(3) for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            body_i = bodies[i]
            body_j = bodies[j]

            # Вектор от i к j (расстояние между телами)
            r_vec = body_j['position'] - body_i['position']
            r = np.linalg.norm(r_vec)

            # Сила гравитации (F = GMm/r^2)
            force_magnitude = (body_i['GM'] * body_j['GM']) / (r ** 2)
            force_dir = r_vec / r #единичный вектор направления силы

            # Ускорения (a = F/m)
            accelerations[i] += force_magnitude / body_i['GM'] * force_dir
            accelerations[j] -= force_magnitude / body_j['GM'] * force_dir

    return accelerations


# Метод Адамса 4-го порядка (предсказание-коррекция)
def adams_bashforth_moulton_4step(bodies, dt, prev_accels):
    n = len(bodies)

    # Шаг 1: Предсказание (Адамс-Башфорт 4-го порядка)
    # Используем предыдущие ускорения для предсказания
    predicted_positions = []
    predicted_velocities = []

    for i in range(n):
        # Коэффициенты для метода Адамса-Башфорта
        v_pred = bodies[i]['velocity'] + dt * (55 / 24 * prev_accels[i][-1]
                                               - 59 / 24 * prev_accels[i][-2]
                                               + 37 / 24 * prev_accels[i][-3]
                                               - 9 / 24 * prev_accels[i][-4])

        r_pred = bodies[i]['position'] + dt * (55 / 24 * bodies[i]['velocity']
                                               - 59 / 24 * bodies[i]['prev_v'][-1]
                                               + 37 / 24 * bodies[i]['prev_v'][-2]
                                               - 9 / 24 * bodies[i]['prev_v'][-3])

        predicted_positions.append(r_pred)
        predicted_velocities.append(v_pred)

    # Сохраняем текущие позиции и скорости для возможного отката
    old_positions = [body['position'].copy() for body in bodies]
    old_velocities = [body['velocity'].copy() for body in bodies]

    # Временно обновляем позиции и скорости для вычисления нового ускорения
    for i in range(n):
        bodies[i]['position'] = predicted_positions[i]
        bodies[i]['velocity'] = predicted_velocities[i]

    # Вычисляем новое ускорение на предсказанной позиции
    new_accel = compute_accelerations(bodies)

    # Шаг 2: Коррекция (Адамс-Моултон 4-го порядка)
    corrected_positions = []
    corrected_velocities = []

    for i in range(n):
        # Коэффициенты для метода Адамса-Моултона
        v_corr = bodies[i]['velocity'] + dt * (9 / 24 * new_accel[i]
                                               + 19 / 24 * prev_accels[i][-1]
                                               - 5 / 24 * prev_accels[i][-2]
                                               + 1 / 24 * prev_accels[i][-3])

        r_corr = bodies[i]['position'] + dt * (9 / 24 * bodies[i]['velocity']
                                               + 19 / 24 * bodies[i]['prev_v'][-1]
                                               - 5 / 24 * bodies[i]['prev_v'][-2]
                                               + 1 / 24 * bodies[i]['prev_v'][-3])

        corrected_positions.append(r_corr)
        corrected_velocities.append(v_corr)

    # Обновляем позиции и скорости
    for i in range(n):
        bodies[i]['position'] = corrected_positions[i]
        bodies[i]['velocity'] = corrected_velocities[i]

        # Сохраняем историю для следующего шага
        bodies[i]['prev_v'].append(old_velocities[i].copy())
        if len(bodies[i]['prev_v']) > 4:
            bodies[i]['prev_v'].pop(0)

    # Обновляем историю ускорений
    final_accel = compute_accelerations(bodies)
    for i in range(n):
        prev_accels[i].append(final_accel[i].copy())
        if len(prev_accels[i]) > 4:
            prev_accels[i].pop(0)

    return final_accel


# Инициализация истории для метода Адамса
def initialize_adams_history(bodies, dt):
    # Для метода Адамса 4-го порядка нам нужно 4 предыдущих значения
    # Используем Рунге-Кутта 4-го порядка для инициализации

    prev_accels = [[] for _ in range(len(bodies))]

    # Первое ускорение
    accel0 = compute_accelerations(bodies)
    for i in range(len(bodies)):
        prev_accels[i].append(accel0[i].copy())
        bodies[i]['prev_v'] = [bodies[i]['velocity'].copy()]

    # Шаг 1: РК4
    k1_pos = [body['velocity'] * dt for body in bodies]
    k1_vel = [a * dt for a in accel0]

    # Сохраняем старые позиции и скорости
    old_positions = [body['position'].copy() for body in bodies]
    old_velocities = [body['velocity'].copy() for body in bodies]

    # Временное обновление для k2
    for i in range(len(bodies)):
        bodies[i]['position'] = old_positions[i] + 0.5 * k1_pos[i]
        bodies[i]['velocity'] = old_velocities[i] + 0.5 * k1_vel[i]

    accel1 = compute_accelerations(bodies)
    k2_pos = [(old_velocities[i] + 0.5 * k1_vel[i]) * dt for i in range(len(bodies))]
    k2_vel = [a * dt for a in accel1]

    # Временное обновление для k3
    for i in range(len(bodies)):
        bodies[i]['position'] = old_positions[i] + 0.5 * k2_pos[i]
        bodies[i]['velocity'] = old_velocities[i] + 0.5 * k2_vel[i]

    accel2 = compute_accelerations(bodies)
    k3_pos = [(old_velocities[i] + 0.5 * k2_vel[i]) * dt for i in range(len(bodies))]
    k3_vel = [a * dt for a in accel2]

    # Временное обновление для k4
    for i in range(len(bodies)):
        bodies[i]['position'] = old_positions[i] + k3_pos[i]
        bodies[i]['velocity'] = old_velocities[i] + k3_vel[i]

    accel3 = compute_accelerations(bodies)
    k4_pos = [(old_velocities[i] + k3_vel[i]) * dt for i in range(len(bodies))]
    k4_vel = [a * dt for a in accel3]

    # Финальное обновление
    for i in range(len(bodies)):
        bodies[i]['position'] = old_positions[i] + (k1_pos[i] + 2 * k2_pos[i] + 2 * k3_pos[i] + k4_pos[i]) / 6
        bodies[i]['velocity'] = old_velocities[i] + (k1_vel[i] + 2 * k2_vel[i] + 2 * k3_vel[i] + k4_vel[i]) / 6
        bodies[i]['prev_v'].append(old_velocities[i].copy())

    # Второе ускорение
    accel1_final = compute_accelerations(bodies)
    for i in range(len(bodies)):
        prev_accels[i].append(accel1_final[i].copy())

    # Повторяем РК4 еще два раза, чтобы получить 4 точки для Адамса
    for _ in range(2):
        k1_pos = [body['velocity'] * dt for body in bodies]
        k1_vel = [compute_accelerations(bodies)[i] * dt for i in range(len(bodies))]

        old_positions = [body['position'].copy() for body in bodies]
        old_velocities = [body['velocity'].copy() for body in bodies]

        for i in range(len(bodies)):
            bodies[i]['position'] = old_positions[i] + 0.5 * k1_pos[i]
            bodies[i]['velocity'] = old_velocities[i] + 0.5 * k1_vel[i]

        accel1 = compute_accelerations(bodies)
        k2_pos = [(old_velocities[i] + 0.5 * k1_vel[i]) * dt for i in range(len(bodies))]
        k2_vel = [a * dt for a in accel1]

        for i in range(len(bodies)):
            bodies[i]['position'] = old_positions[i] + 0.5 * k2_pos[i]
            bodies[i]['velocity'] = old_velocities[i] + 0.5 * k2_vel[i]

        accel2 = compute_accelerations(bodies)
        k3_pos = [(old_velocities[i] + 0.5 * k2_vel[i]) * dt for i in range(len(bodies))]
        k3_vel = [a * dt for a in accel2]

        for i in range(len(bodies)):
            bodies[i]['position'] = old_positions[i] + k3_pos[i]
            bodies[i]['velocity'] = old_velocities[i] + k3_vel[i]

        accel3 = compute_accelerations(bodies)
        k4_pos = [(old_velocities[i] + k3_vel[i]) * dt for i in range(len(bodies))]
        k4_vel = [a * dt for a in accel3]

        for i in range(len(bodies)):
            bodies[i]['position'] = old_positions[i] + (k1_pos[i] + 2 * k2_pos[i] + 2 * k3_pos[i] + k4_pos[i]) / 6
            bodies[i]['velocity'] = old_velocities[i] + (k1_vel[i] + 2 * k2_vel[i] + 2 * k3_vel[i] + k4_vel[i]) / 6
            bodies[i]['prev_v'].append(old_velocities[i].copy())

        next_accel = compute_accelerations(bodies)
        for i in range(len(bodies)):
            prev_accels[i].append(next_accel[i].copy())

    return prev_accels


# Вычисление инвариантов (энергии и момента импульса)
def compute_invariants(bodies):
    # Полная энергия (кинетическая + потенциальная)
    kinetic = 0.0
    potential = 0.0

    for i in range(len(bodies)):
        kinetic += 0.5 * bodies[i]['GM'] * np.sum(bodies[i]['velocity'] ** 2)

        for j in range(i + 1, len(bodies)):
            r = np.linalg.norm(bodies[i]['position'] - bodies[j]['position'])
            potential -= bodies[i]['GM'] * bodies[j]['GM'] / r

    total_energy = kinetic + potential

    # Момент импульса
    angular_momentum = np.zeros(3)
    for body in bodies:
        angular_momentum += body['GM'] * np.cross(body['position'], body['velocity'])

    return total_energy, angular_momentum


# Основная функция симуляции
def simulate_nbody(filename, days=365, dt=1.0):
    bodies = read_initial_conditions(filename)

    # Инициализируем историю для метода Адамса
    prev_accels = initialize_adams_history(bodies, dt)

    # Сохраняем начальные инварианты
    initial_energy, initial_ang_mom = compute_invariants(bodies)
    energies = [initial_energy]
    ang_moms = [np.linalg.norm(initial_ang_mom)]

    # Сохраняем траектории
    for body in bodies:
        body['trajectory'].append(body['position'].copy())

    # Основной цикл симуляции
    for day in range(1, int(days / dt) + 1):
        # Выполняем шаг метода Адамса
        adams_bashforth_moulton_4step(bodies, dt, prev_accels)

        # Сохраняем траектории
        for body in bodies:
            body['trajectory'].append(body['position'].copy())

        # Вычисляем и сохраняем инварианты
        current_energy, current_ang_mom = compute_invariants(bodies)
        energies.append(current_energy)
        ang_moms.append(np.linalg.norm(current_ang_mom))

    # Вычисляем относительные изменения инвариантов
    energy_change = np.abs((np.array(energies) - initial_energy)) / np.abs(initial_energy)
    ang_mom_change = np.abs((np.array(ang_moms) - ang_moms[0])) / ang_moms[0]

    return bodies, energy_change, ang_mom_change

def plot_trajectories(bodies):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    colors = plt.cm.tab20(np.linspace(0, 1, len(bodies)))

    for i, body in enumerate(bodies):
        if body['name'] == 'Sun':
            color = 'yellow'
            size = 100
        elif body['name'] == 'Earth':
            color = 'blue'
            size = 20
        else:
            color = colors[i]
            size = 10

        trajectory = np.array(body['trajectory'])
        ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                color=color, alpha=0.7, linewidth=1, label=body['name'])
        ax.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2],
                   color=color, s=size)

    ax.set_xlabel('X (au)')
    ax.set_ylabel('Y (au)')
    ax.set_zlabel('Z (au)')
    ax.set_title('Траектории тел Солнечной системы')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


def plot_invariants(energy_change, ang_mom_change):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # График энергии
    ax1.plot(energy_change)
    ax1.set_yscale('log')
    ax1.set_title('Относительное изменение полной энергии системы')
    ax1.set_ylabel('ΔE/E')
    ax1.grid(True)

    # График момента импульса
    ax2.plot(ang_mom_change)
    ax2.set_yscale('log')
    ax2.set_title('Относительное изменение момента импульса системы')
    ax2.set_xlabel('Шаг интегрирования')
    ax2.set_ylabel('ΔL/L')
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


def plot_trajectories(bodies, zoom_inner=True):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    inner_planets = ['Sun', 'Mercury', 'Venus', 'Earth', 'Mars']
    colors = plt.cm.tab20(np.linspace(0, 1, len(bodies)))

    for i, body in enumerate(bodies):
        # Настройки внешнего вида
        if body['name'] == 'Sun':
            color = 'yellow'
            size = 150
            alpha = 1.0
        elif body['name'] in inner_planets:
            color = colors[i]
            size = 30
            alpha = 0.9
        else:  # Внешние планеты
            color = colors[i]
            size = 15
            alpha = 0.6

        trajectory = np.array(body['trajectory'])

        # Для внешних планет рисуем только последний отрезок траектории
        if body['name'] not in inner_planets:
            trajectory = trajectory[-1000:]  # Последние 1000 точек

        ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                color=color, alpha=alpha, linewidth=1)
        ax.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2],
                   color=color, s=size, label=body['name'])

    # Настройка масштаба
    if zoom_inner:
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        ax.set_zlim([-1, 1])
        title = "Траектории внутренних планет (увеличенный масштаб)"
    else:
        max_val = 35  # Для показа внешних планет
        ax.set_xlim([-max_val, max_val])
        ax.set_ylim([-max_val, max_val])
        ax.set_zlim([-max_val / 2, max_val / 2])
        title = "Траектории всех тел Солнечной системы"

    ax.set_xlabel('X (а.е.)')
    ax.set_ylabel('Y (а.е.)')
    ax.set_zlabel('Z (а.е.)')
    ax.set_title(title)

    # Размещаем легенду с двумя колонками
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2)
    plt.tight_layout()
    plt.show()


def animate_trajectories(bodies, frames=200, zoom_inner=True):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Подготовка данных
    trajectories = [np.array(body['trajectory']) for body in bodies]
    max_points = max(len(traj) for traj in trajectories)
    step = max(1, max_points // frames)

    # Настройка масштаба
    if zoom_inner:
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        ax.set_zlim([-1, 1])
    else:
        max_val = 35
        ax.set_xlim([-max_val, max_val])
        ax.set_ylim([-max_val, max_val])
        ax.set_zlim([-max_val / 2, max_val / 2])

    # Создание графических элементов
    inner_planets = ['Sun', 'Mercury', 'Venus', 'Earth', 'Mars']
    lines = []
    points = []
    labels = []

    for i, body in enumerate(bodies):
        # Настройки внешнего вида
        if body['name'] == 'Sun':
            color = 'yellow'
            size = 20
            text_size = 10
        elif body['name'] in inner_planets:
            color = plt.cm.tab20(i)
            size = 10
            text_size = 8
        else:
            color = plt.cm.tab20(i)
            size = 5
            text_size = 6

        line, = ax.plot([], [], [], color=color, alpha=0.7, linewidth=1)
        point, = ax.plot([], [], [], 'o', color=color, markersize=size)
        label = ax.text(0, 0, 0, body['name'], fontsize=text_size,
                        bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

        lines.append(line)
        points.append(point)
        labels.append(label)

    def update(frame):
        current_idx = min(frame * step, max_points - 1)

        for i, traj in enumerate(trajectories):
            # Для внешних планет показываем только последний отрезок
            if bodies[i]['name'] not in inner_planets:
                start_idx = max(0, current_idx - 500)  # Показываем последние 500 точек
                x, y, z = traj[start_idx:current_idx + 1].T
            else:
                x, y, z = traj[:current_idx + 1].T

            lines[i].set_data(x, y)
            lines[i].set_3d_properties(z)

            if current_idx < len(traj):
                points[i].set_data([x[-1]], [y[-1]])
                points[i].set_3d_properties([z[-1]])
                labels[i].set_position((x[-1], y[-1], z[-1]))
                labels[i].set_visible(True)
            else:
                labels[i].set_visible(False)

        title = "Движение внутренних планет" if zoom_inner else "Движение всех тел"
        ax.set_title(f'{title} (день {current_idx})')
        return lines + points + labels

    ani = FuncAnimation(fig, update, frames=frames, interval=100, blit=True)
    plt.tight_layout()
    plt.show()
    return ani


if __name__ == "__main__":
    # Параметры симуляции
    simulation_days = 365 * 5  # 5 лет
    time_step = 0.5  # Шаг в 0.5 дня

    # Запуск симуляции
    bodies, energy_change, ang_mom_change = simulate_nbody("points.txt", simulation_days, time_step)

    # Графики траекторий
    plot_trajectories(bodies, zoom_inner=True)  # Внутренние планеты
    plot_trajectories(bodies, zoom_inner=False)  # Все планеты

    # Анимации
    animate_trajectories(bodies, frames=300, zoom_inner=True)  # Внутренние
    animate_trajectories(bodies, frames=300, zoom_inner=False)  # Все планеты

    # Графики сохранения инвариантов
    plot_invariants(energy_change, ang_mom_change)