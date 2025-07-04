import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation

# Загрузка начальных данных
def load_bodies(filename):
    names, masses, positions, velocities = [], [], [], []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.split()
            names.append(parts[0])
            masses.append(float(parts[1]))
            positions.append([float(parts[2]), float(parts[3]), float(parts[4])])
            velocities.append([float(parts[5]), float(parts[6]), float(parts[7])])
    return names, np.array(masses), np.array(positions), np.array(velocities)

# Гравитационное ускорение
def compute_accelerations(pos, masses, G=1.0):
    N = len(masses)
    acc = np.zeros_like(pos)
    for i in range(N):
        for j in range(N):
            if i != j:
                r = pos[j] - pos[i]
                dist = np.linalg.norm(r) + 1e-10  # избежание деления на 0
                acc[i] += G * masses[j] * r / dist**3
    return acc

# Метод Адамса-Бэшфорта 4-го порядка
class AdamsBashforth4:
    def __init__(self, masses, pos0, vel0, dt):
        self.masses = masses
        self.pos = [pos0]
        self.vel = [vel0]
        self.acc = [compute_accelerations(pos0, masses)]
        self.dt = dt

        # Расчёт первых 3 шагов с RK4
        for _ in range(3):
            p, v = self.rk4_step(self.pos[-1], self.vel[-1], self.masses, self.dt)
            self.pos.append(p)
            self.vel.append(v)
            self.acc.append(compute_accelerations(p, masses))

    def rk4_step(self, pos, vel, masses, dt):
        a1 = compute_accelerations(pos, masses)
        k1v = a1
        k1x = vel

        a2 = compute_accelerations(pos + 0.5 * dt * k1x, masses)
        k2v = a2
        k2x = vel + 0.5 * dt * k1v

        a3 = compute_accelerations(pos + 0.5 * dt * k2x, masses)
        k3v = a3
        k3x = vel + 0.5 * dt * k2v

        a4 = compute_accelerations(pos + dt * k3x, masses)
        k4v = a4
        k4x = vel + dt * k3v

        new_pos = pos + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
        new_vel = vel + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)

        return new_pos, new_vel

    def step(self):
        a = self.acc
        v_next = self.vel[-1] + self.dt / 24 * (55 * a[-1] - 59 * a[-2] + 37 * a[-3] - 9 * a[-4])
        x_next = self.pos[-1] + self.dt / 24 * (55 * self.vel[-1] - 59 * self.vel[-2] + 37 * self.vel[-3] - 9 * self.vel[-4])
        a_next = compute_accelerations(x_next, self.masses)

        self.pos.append(x_next)
        self.vel.append(v_next)
        self.acc.append(a_next)

        # Удалим старые значения, чтобы сохранять только 4 последних шага
        self.pos = self.pos[-4:]
        self.vel = self.vel[-4:]
        self.acc = self.acc[-4:]

        return x_next, v_next

# Инварианты: полная энергия и момент импульса
def compute_energy_and_angular_momentum(pos, vel, masses):
    kinetic = 0.5 * np.sum(masses[:, None] * np.sum(vel**2, axis=1))
    potential = 0.0
    L = np.zeros(3)
    N = len(masses)
    for i in range(N):
        for j in range(i + 1, N):
            r = np.linalg.norm(pos[i] - pos[j]) + 1e-10
            potential -= masses[i] * masses[j] / r
        L += np.cross(pos[i], masses[i] * vel[i])
    return kinetic + potential, L

# Основной цикл
def simulate(filename='points.txt', steps=3000, dt=0.5):
    names, masses, pos0, vel0 = load_bodies(filename)
    integrator = AdamsBashforth4(masses, pos0, vel0, dt)

    N = len(masses)
    trajectories = [np.zeros((steps, 3)) for _ in range(N)]
    energies = np.zeros(steps)
    angular_momenta = np.zeros(steps)

    for step in range(steps):
        pos, vel = integrator.step()
        for i in range(N):
            trajectories[i][step] = pos[i]
        E, L = compute_energy_and_angular_momentum(pos, vel, masses)
        energies[step] = E
        angular_momenta[step] = np.linalg.norm(L)

    return names, np.array(trajectories), energies, angular_momenta


# Визуализация
def plot_trajectories(names, trajectories):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    for name, traj in zip(names, trajectories):
        traj = np.array(traj)
        ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], label=name)
    ax.set_title("Траектории тел")
    ax.set_xlabel("x [AU]")
    ax.set_ylabel("y [AU]")
    ax.set_zlabel("z [AU]")
    ax.legend()
    plt.show()

def plot_invariants(energies, angular_momenta):
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(energies)
    ax[0].set_title("Полная энергия системы")
    ax[1].plot(angular_momenta)
    ax[1].set_title("Модуль момента импульса")
    ax[1].set_xlabel("Шаги времени")
    plt.tight_layout()
    plt.show()

def animate_trajectories(names, trajectories, interval=30):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    N = len(names)
    lines = [ax.plot([], [], [], label=names[i])[0] for i in range(N)]
    points = [ax.plot([], [], [], 'o')[0] for _ in range(N)]

    max_range = np.max(np.abs(trajectories))
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    ax.set_title("Анимация движения тел")
    ax.set_xlabel("X [AU]")
    ax.set_ylabel("Y [AU]")
    ax.set_zlabel("Z [AU]")
    ax.legend()

    def update(frame):
        for i in range(N):
            lines[i].set_data(trajectories[i][:frame+1, 0], trajectories[i][:frame+1, 1])
            lines[i].set_3d_properties(trajectories[i][:frame+1, 2])
            points[i].set_data([trajectories[i][frame, 0]], [trajectories[i][frame, 1]])
            points[i].set_3d_properties([trajectories[i][frame, 2]])
        return lines + points

    ani = animation.FuncAnimation(fig, update, frames=trajectories[0].shape[0], interval=interval, blit=True)
    plt.show()

# Запуск
if __name__ == '__main__':
    names, trajectories, energies, angular_momenta = simulate(steps=2000, dt=0.5)
    animate_trajectories(names, trajectories)
    plot_invariants(energies, angular_momenta)

