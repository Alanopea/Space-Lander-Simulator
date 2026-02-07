import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

# Use project's PID controller
from core.controllers.pid_controller import PIDController

# -------------------------------------------------------
# PID Controller Gains (initial)
# -------------------------------------------------------
Kp = 8.0
Ki = 1.5
Kd = 3.0

# -------------------------------------------------------
# Simulation variables
# -------------------------------------------------------
dt = 0.02
x = 0.0
v = 0.0

target = 0.0

# Instantiate PID controller from project
controller = PIDController(Kp, Ki, Kd, setpoint=target, output_limits=None)

capture_mode = False
capturing = False
capture_data = {
    "t": [],
    "x": [],
    "v": [],
    "error": [],
    "u": [],
    "P": [],
    "I": [],
    "D": []
}
t_sim = 0.0

# -------------------------------------------------------
# Click handler
# -------------------------------------------------------
def onclick(event):
    global target, capturing, capture_mode, capture_data

    if event.inaxes is None:
        return

    # Normal mode: free clicking
    if not capture_mode:
        target = event.xdata
        return

    # Capture mode: accept only ONE click, then simulate until stop
    if capture_mode and not capturing:
        target = event.xdata
        # update controller setpoint immediately
        controller.setpoint = target
        capturing = True
        capture_data = {k: [] for k in capture_data}  # reset buffers


# -------------------------------------------------------
# Button handler
# -------------------------------------------------------
def start_capture(event):
    global capture_mode, capturing
    capture_mode = True
    capturing = False
    print("Capture mode activated: click once to choose target.")


# -------------------------------------------------------
# Plot captured data
# -------------------------------------------------------
def show_plots():
    # ============================================================
    # WINDOW 1: Position, Velocity, Error (three stacked plots)
    # ============================================================
    fig1 = plt.figure(figsize=(10, 9))
    fig1.suptitle("PID State Response", fontsize=16)

    axs1 = fig1.subplots(3, 1, sharex=True)

    # --- Position ---
    axs1[0].plot(capture_data["t"], capture_data["x"], label="Position x")
    axs1[0].axhline(capture_data["x"][-1], linestyle='--', color='gray', linewidth=1)
    axs1[0].set_ylabel("Position [m]")
    axs1[0].grid(True)

    # --- Velocity ---
    axs1[1].plot(capture_data["t"], capture_data["v"], label="Velocity v")
    axs1[1].set_ylabel("Velocity [m/s]")
    axs1[1].grid(True)

    # --- Error ---
    axs1[2].plot(capture_data["t"], capture_data["error"], label="Tracking Error")
    axs1[2].set_ylabel("Error [m]")
    axs1[2].set_xlabel("Time [s]")
    axs1[2].grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

    # ============================================================
    # WINDOW 2: Control Input (u) and P/I/D Terms
    # ============================================================
    fig2 = plt.figure(figsize=(10, 6))
    fig2.suptitle("PID Control Input Breakdown", fontsize=16)

    ax2 = fig2.add_subplot(1,1,1)

    ax2.plot(capture_data["t"], capture_data["u"], label="Control Input u", linewidth=2)
    ax2.plot(capture_data["t"], capture_data["P"], label="P term", linestyle='--')
    ax2.plot(capture_data["t"], capture_data["I"], label="I term", linestyle='--')
    ax2.plot(capture_data["t"], capture_data["D"], label="D term", linestyle='--')

    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Control Signal")
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


# -------------------------------------------------------
# Figure and GUI setup
# -------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 3))
plt.subplots_adjust(left=0.1, bottom=0.35)

ax.set_xlim(-5, 5)
ax.set_ylim(-1, 1)
ax.plot([-5, 5], [0, 0], 'k-', linewidth=1)

cart_marker, = ax.plot([], [], 'ks', markersize=12)
target_marker, = ax.plot([], [], 'ro', markersize=6)
text_box = ax.text(-4.8, 0.7, "", fontsize=10, family='monospace')

fig.canvas.mpl_connect('button_press_event', onclick)

# -------------------------------------------------------
# Sliders for PID tuning
# -------------------------------------------------------
ax_kp = plt.axes([0.1, 0.22, 0.8, 0.03])
ax_ki = plt.axes([0.1, 0.17, 0.8, 0.03])
ax_kd = plt.axes([0.1, 0.12, 0.8, 0.03])

slider_kp = Slider(ax_kp, "Kp", 0.0, 20.0, valinit=Kp)
slider_ki = Slider(ax_ki, "Ki", 0.0, 10.0, valinit=Ki)
slider_kd = Slider(ax_kd, "Kd", 0.0, 10.0, valinit=Kd)

ax_desc = plt.axes([0.1, 0.04, 0.8, 0.06])
ax_desc.axis("off")
ax_desc.text(
    0.0, 0.5,
    "Kp: proportional correction (faster but more overshoot)\n"
    "Ki: removes steady-state error (too high → windup)\n"
    "Kd: damping term (reduces oscillation)",
    fontsize=9, family='monospace'
)

# -------------------------------------------------------
# Capture button
# -------------------------------------------------------
button_ax = plt.axes([0.45, 0.005, 0.15, 0.04])
button = Button(button_ax, "Capture Plots")
button.on_clicked(start_capture)

# -------------------------------------------------------
# Animation update
# -------------------------------------------------------
def update(frame):
    global x, v, e_int, e_prev, Kp, Ki, Kd, t_sim
    global capture_mode, capturing

    # Read slider values
    Kp = slider_kp.val
    Ki = slider_ki.val
    Kd = slider_kd.val

    # PID control via project PIDController
    # update controller gains live
    controller.kp = Kp
    controller.ki = Ki
    controller.kd = Kd
    controller.setpoint = target

    # compute error and approximate PID terms (pre-update) for display
    error = controller.setpoint - x
    derivative = (error - controller.prev_error) / dt if dt > 0 else 0.0
    P = controller.kp * error
    # approximate integral term (what it will be after update)
    I = controller.ki * (controller.integral + error * dt)
    D = controller.kd * derivative

    # get controller output (this updates internal integral / prev_error)
    u = controller.update(x, dt)

    # Physics update
    v += u * dt
    x += v * dt
    t_sim += dt

    # Draw
    cart_marker.set_data([x], [0])
    target_marker.set_data([target], [0])

    text_box.set_text(
        f"target: {target: .2f}\n"
        f"x: {x: .2f}\n"
        f"v: {v: .2f}\n\n"
        f"error: {error: .3f}\n"
        f"P: {P: .3f}\n"
        f"I: {I: .3f}\n"
        f"D: {D: .3f}\n"
        f"u: {u: .3f}"
    )

    # --------------------------------------------
    # Capture mode logic
    # --------------------------------------------
    if capturing:
        capture_data["t"].append(t_sim)
        capture_data["x"].append(x)
        capture_data["v"].append(v)
        capture_data["error"].append(error)
        capture_data["u"].append(u)
        capture_data["P"].append(P)
        capture_data["I"].append(I)
        capture_data["D"].append(D)

        # Stop conditions
        reached = abs(error) < 0.01 and abs(v) < 0.01
        too_long = t_sim - capture_data["t"][0] > 10.0

        if reached or too_long:
            capturing = False
            capture_mode = False
            show_plots()

    return cart_marker, target_marker, text_box


ani = FuncAnimation(fig, update, interval=20, blit=False, cache_frame_data=False)
plt.show()
