# Space Lander Simulator: Comparative Analysis of Control Algorithms in Virtual Planetary Environments

## Abstract

This engineering thesis presents a comprehensive space lander simulator developed in Python, designed to model and analyze spacecraft descent and landing across multiple planetary environments. The simulator implements a high-fidelity physics engine that accounts for translational and rotational dynamics, spatial orientation, fuel consumption, and thruster operation. Three distinct control algorithms—classical Proportional-Integral-Derivative (PID), Linear Quadratic Regulator (LQR), and Model Predictive Control (MPC)—are implemented, tested, and compared across Earth, Moon, and Mars environments. The thesis includes investigation of emergency scenarios (engine failures, response delays) and provides evidence-based recommendations for mission-critical control system selection. This project demonstrates the application of modern control theory and optimization techniques to real-world aerospace engineering challenges.

**Keywords:** Space vehicle guidance, Control systems, PID control, Linear Quadratic Regulator, Model Predictive Control, Emergency scenario analysis, Multi-planetary simulation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Physics Engine](#physics-engine)
4. [Control Algorithms](#control-algorithms)
5. [Planetary Models](#planetary-models)
6. [Emergency Scenarios](#emergency-scenarios)
7. [Experiments & Results](#experiments--results)
8. [Installation & Setup](#installation--setup)
9. [Usage Guide](#usage-guide)
10. [Technical Documentation](#technical-documentation)
11. [Results & Conclusions](#results--conclusions)

---

## Project Overview

### Thesis Objective

The goal of this engineering thesis is to:

- **Design and implement** a realistic space lander simulator incorporating motion physics, mass properties, spatial orientation, and thruster dynamics
- **Implement multiple control algorithms** (PID, LQR, MPC) with distinct design philosophies and performance characteristics
- **Compare and evaluate** control algorithm effectiveness across metrics: landing precision, fuel efficiency, stability, and robustness
- **Test system behavior** under nominal and emergency scenarios across three representative planetary environments
- **Provide engineering recommendations** for mission-critical control system selection based on quantitative analysis

### Research Questions

1. How do classical (PID) and modern optimal control methods (LQR, MPC) compare in terms of fuel efficiency and landing precision?
2. What is the impact of engine failures and response delays on mission success rates?
3. Which control algorithm is most robust across varying planetary gravity conditions?
4. What are the critical failure modes and parameters that lead to mission abort?

### Scope

- **Planets**: Earth (g=9.81 m/s²), Moon (g=1.62 m/s²), Mars (g=3.71 m/s²)
- **Lander Models**: Falcon 9, Moon Lander (with customizable configurations)
- **Emergency Scenarios**: Single/dual engine failures, stuck engines, response lag (1-5s delays)
- **Performance Metrics**: Landing velocity, fuel consumption, descent time, control stability, trajectory tracking error

---

## System Architecture

### Directory Structure

```
.
├── core/                           # Core simulation engine
│   ├── Simulator.py               # Main simulation orchestrator
│   ├── PhysicsEngine.py           # Physics calculations (forces, torques, dynamics)
│   ├── RigidBody.py               # Rigid body dynamics
│   ├── ThrustManager.py           # Thrust allocation management
│   ├── ThrustAllocator.py         # Optimal thrust allocation solver
│   ├── FuelManager.py             # Fuel consumption tracking
│   ├── DataLogger.py              # Telemetry logging
│   ├── config.py                  # Global configuration and defaults
│   ├── EnvironmentManager.py      # Planet definitions and properties
│   ├── LanderManager.py           # Lander model factory
│   │
│   ├── controllers/               # Control algorithm implementations
│   │   ├── IController.py         # Abstract controller interface
│   │   ├── pid_controller.py      # PID controller with anti-windup
│   │   ├── LQRController.py       # Linear Quadratic Regulator
│   │   ├── MPCController.py       # Model Predictive Control
│   │   ├── controller_factory.py  # Factory for instantiating controllers
│   │
│   ├── Landers/                   # Lander model definitions
│   │   ├── Lander.py              # Abstract base lander class
│   │   ├── Engine.py              # Engine thrust model
	│   │   ├── Falcon9Booster.py      # Falcon 9 configuration
│   │   ├── MoonLander.py          # Apollo-style moon lander
│   │
│   └── emergencies/               # Emergency scenario handling
│       ├── EmergencyScenarioManager.py    # Scenario definitions
│       ├── EmergencyScenarioHandler.py    # Scenario logic (failures, lag)
│
├── UI/                            # User interface (PyQt5-based)
│   ├── dashboard_UI.py            # Main dashboard widget
│   ├── panels/                    # Individual dashboard panels
│   │   ├── status_panel_UI.py     # Landing status indicator
│   │   ├── telemetry_panel_UI.py  # Telemetry display
│   │   ├── radar_panel_UI.py      # Top-down radar visualization
│   │   ├── emergency_panel_UI.py  # Emergency log and alerts
│   │   ├── simulation_panel_UI.py # Simulation controls
│   │   ├── lander_3d_panel_UI.py  # 3D lander visualization
│   │   └── EnginePanelUI.py       # Engine throttle visualization
│
├── ui_integration/                # UI-simulation bridge
│   ├── interfaces.py              # ISimulator interface
│   ├── step_simulator.py          # Stepping simulator wrapper
│   ├── simulation_worker.py       # Worker thread for simulations
│
├── experiments/                   # Research experiments and analyses
│   ├── controller_comparison_experiment.py  # Controller performance comparison
│   ├── emergency_scenario_experiment.py     # Emergency robustness analysis
│   ├── PID_presentation.py        # Interactive PID tuning demo
│   ├── LQR_presentation.py        # Interactive LQR tuning demo
│   └── comparison_results/        # Generated plots and data
│
├── app.py                         # Dashboard application entry point
├── main.py                        # Command-line simulator entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Core Components

#### Simulator
The `Simulator` class is the main orchestrator, managing all physics calculations, control loops, and state propagation:
- Integrates controller, physics engine, fuel manager, and thrust allocator
- Implements step-by-step simulation with configurable timestep
- Supports both autonomous (controller-based) and manual thrust control

#### Physics Engine
The `PhysicsEngine` handles all physical interactions:
- **Translational dynamics**: Gravity, thrust, atmospheric drag with body-referenced rotation
- **Rotational dynamics**: Torque from asymmetric drag and engine imbalance
- **Attitude integration**: Euler angle updates from angular velocity
- **Coordinate transformation**: Body-frame to world-frame thrust rotation using ZYX Euler angles

#### Thrust Allocator
The `ThrustAllocator` solves the thrust distribution problem:
- Translates desired force and torque into per-engine thrust commands
- Implements least-squares solver with inequality constraints (0 ≤ thrust ≤ max)
- Includes redistribution logic for fuel-constrained and failed-engine scenarios

#### Control Algorithms
Three distinct control approaches are implemented:
- **PID**: Proportional-Integral-Derivative with anti-windup
- **LQR**: Optimal state feedback via continuous-time Algebraic Riccati Equation
- **MPC**: Finite-horizon optimal control with constraints

---

## Physics Engine

### Coordinate System Definitions

#### Inertial Frame (World Frame)
- **Origin**: Planetary surface landing point (altitude = 0)
- **X-axis**: Horizontal (east)
- **Y-axis**: Vertical (up)
- **Z-axis**: Horizontal (north)
- **Vectors**: Position, velocity, acceleration in world coordinates

#### Body-Fixed Frame
- **Origin**: Lander center of mass
- **X-axis**: Lateral (rightward)
- **Y-axis**: Vertical (upward through body)
- **Z-axis**: Longitudinal (forward)
- **Application**: Engine positions/directions defined here

### Transformation Between Frames

Orientation is represented as Euler angles: **[pitch, roll, yaw]** (radians)

The body-to-world rotation matrix is computed using **ZYX Euler convention**:

$$R = R_z(\text{yaw}) \cdot R_y(\text{pitch}) \cdot R_x(\text{roll})$$

Thrust vectors are computed in body frame and rotated to world frame:

$$\mathbf{F}_{\text{world}} = R \cdot \mathbf{F}_{\text{body}}$$

### Equations of Motion

**Translational dynamics**:
$$\mathbf{a} = \frac{\mathbf{F}_{\text{thrust}} + \mathbf{F}_{\text{drag}} + \mathbf{F}_{\text{gravity}}}{m}$$

**Rotational dynamics**:
$$\boldsymbol{\alpha} = \mathbf{I}^{-1} \cdot \boldsymbol{\tau}$$

Where:
- $\mathbf{a}$ = linear acceleration
- $\mathbf{F}_{\text{thrust}}$ = net engine thrust in world frame
- $\mathbf{F}_{\text{drag}}$ = aerodynamic drag (proportional to velocity²)
- $\mathbf{F}_{\text{gravity}}$ = gravitational force [0, -mg, 0]
- $\boldsymbol{\alpha}$ = angular acceleration
- $\mathbf{I}$ = moment of inertia tensor (cuboid approximation)
- $\boldsymbol{\tau}$ = torque from drag and unbalanced thrust

---

## Control Algorithms

### PID Controller

**Purpose**: Classical feedback control with intuitive gain tuning

**Implementation**:
```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de/dt
```

**Features**:
- Proportional term: Immediate correction proportional to error
- Integral term: Elimination of steady-state error with anti-windup protection
- Derivative term: Damping to reduce overshoot
- Output limiting: Saturation to physical actuator constraints

**Configuration** (`config.py`):
```python
PID_DEFAULTS = {
    'Kp': 8.0,      # Proportional gain
    'Ki': 1.5,      # Integral gain
    'Kd': 3.0,      # Derivative gain
}
```

**Advantages**: 
- Robust, widely understood
- Fast computation
- Good for well-damped systems

**Disadvantages**: 
- Manual tuning required
- No explicit constraint handling
- Reactive rather than predictive

### LQR Controller

**Purpose**: Optimal state feedback via dynamic programming

**Implementation**:
Solves continuous-time Algebraic Riccati Equation (CARE):
$$\mathbf{A}^T \mathbf{P} + \mathbf{P} \mathbf{A} - \mathbf{P} \mathbf{B} \mathbf{R}^{-1} \mathbf{B}^T \mathbf{P} + \mathbf{Q} = 0$$

Optimal control law:
$$u = -\mathbf{K} \mathbf{x} \text{ where } \mathbf{K} = \mathbf{R}^{-1} \mathbf{B}^T \mathbf{P}$$

**State Space Model**:
$$\begin{bmatrix} \dot{x} \\ \dot{v} \end{bmatrix} = \begin{bmatrix} 0 & 1 \\ 0 & 0 \end{bmatrix} \begin{bmatrix} x \\ v \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} u$$

Where x = position error, v = velocity error

**Configuration** (`config.py`):
```python
LQR_DEFAULTS = {
    'Q': diag([0.01, 200.0]),  # State cost (position, velocity)
    'R': [1.0],                 # Control effort cost
}
```

**Advantages**:
- Mathematically optimal for linear systems
- Excellent disturbance rejection
- Systematic weight tuning via Q/R matrices

**Disadvantages**: 
- Requires linearization
- No explicit constraint handling
- Sensitive to model accuracy

### MPC Controller

**Purpose**: Finite-horizon optimal control with explicit constraints

**Implementation**:
$$\min_{\mathbf{u}} \sum_{k=0}^{N-1} \left( \mathbf{x}_k^T \mathbf{Q} \mathbf{x}_k + \mathbf{u}_k^T \mathbf{R} \mathbf{u}_k \right) + \mathbf{x}_N^T \mathbf{P} \mathbf{x}_N$$

Subject to:
$$\mathbf{x}_{k+1} = \mathbf{A} \mathbf{x}_k + \mathbf{B} \mathbf{u}_k$$
$$u_{\min} \leq \mathbf{u}_k \leq u_{\max}$$
$$|\Delta u_k| \leq \Delta u_{\max}$$ (rate limit)

**Features**:
- Receding horizon optimization (N=20 steps)
- Hard constraints on throttle (0-100%)
- Rate limiting to prevent abrupt thrust changes
- Qp solver for efficient online computation

**Configuration** (`config.py`):
```python
MPC_DEFAULTS = {
    'N': 20,                         # Prediction horizon
    'Q': diag([10.0, 1.0]),         # State weights
    'R': [0.1],                      # Control weight
    'u_limits': (0.0, 1.0),         # Throttle bounds
    'rate_limit': 0.5,              # Max throttle change per step
}
```

**Advantages**:
- Handles explicit constraints naturally
- Proactive (looks ahead N steps)
- Best tracking accuracy in practice

**Disadvantages**:
- Computationally expensive (quadratic programming)
- Requires accurate forward model
- Slower control update

---

## Planetary Models

Three representative planetary environments are modeled:

| Property | Earth | Moon | Mars |
|----------|-------|------|------|
| Surface Gravity (m/s²) | 9.81 | 1.62 | 3.71 |
| Atmosphere Density (kg/m³) | 1.225 | 0.0 | 0.020 |
| Gravity Model | Constant | Constant | Constant |
| Atmosphere Model | Exponential (optional) | None | Thin CO₂ |

**Gravity variation with altitude** (where applicable):
$$g(h) = g_0 \left( \frac{R}{R+h} \right)^2$$

**Atmospheric drag** (only on Earth/Mars):
$$\mathbf{F}_{\text{drag}} = -\frac{1}{2} \rho C_d \mathbf{v} \|\mathbf{v}\|$$

Where:
- ρ = air density
- $C_d$ = drag coefficient (0.47 for sphere, vehicle-specific)
- v = relative velocity

---

## Emergency Scenarios

Six emergency scenarios are tested to evaluate robustness:

### 1. One Engine Failure
- **Severity**: 25% thrust loss (1 of 4 engines disabled)
- **Challenge**: Asymmetric thrust requires torque compensation
- **Failure Mode**: Spiral descent if not corrected

### 2. Two Engine Failures
- **Severity**: 50% thrust loss (2 of 4 engines disabled)
- **Challenge**: Severe thrust deficit
- **Failure Mode**: Uncontrolled descent, likely crash

### 3. One Engine Stuck at 100%
- **Severity**: Uncontrolled thrust in one direction
- **Challenge**: Extreme asymmetric thrust and torque
- **Failure Mode**: Loss of roll/pitch control

### 4. Response Lag: Mild (1.0s)
- **Severity**: 1-second delay between command and throttle change
- **Challenge**: Requires anticipatory control
- **Failure Mode**: Overshoot, oscillations

### 5. Response Lag: Medium (2.0s)
- **Severity**: 2-second delay (realistic for complex systems)
- **Challenge**: Significantly more difficult to predict
- **Failure Mode**: Instability, large excursions

### 6. Response Lag: Severe (5.0s)
- **Severity**: 5-second delay (extreme, for robustness assessment)
- **Challenge**: System behaves as open-loop for critical maneuvers
- **Failure Mode**: Very likely mission failure

Each scenario is tested on all three controllers to assess robustness.

---

## Experiments & Results

### Experiment 1: Controller Comparison

**Purpose**: Compare controller performance across planets under nominal conditions

**Execution**:
```bash
python experiments/controller_comparison_experiment.py
```

**Conditions**:
- Initial altitude: 500 m
- Initial velocity: -50 m/s (descending)
- Target landing velocity: -5 m/s
- All engines operational
- No response delays

**Metrics Calculated**:
1. Landing precision (final velocity error)
2. Fuel consumption (kg)
3. Descent time (s)
4. Control effort (throttle variance)
5. Trajectory smoothness

**Output**: Comparison plots for Earth, Moon, Mars
- Velocity vs. time
- Altitude vs. time
- Throttle commands
- Fuel consumption curves

### Experiment 2: Emergency Scenario Analysis

**Purpose**: Evaluate controller robustness under failure conditions

**Execution**:
```bash
python experiments/emergency_scenario_experiment.py
```

**Conditions**:
- Platform: Falcon 9 on Earth
- Controller: MPC (best performer from Experiment 1)
- Test all 6 emergency scenarios
- Initial conditions: 500 m altitude, -50 m/s velocity

**Metrics Calculated**:
1. **Success/Failure**: Safe landing (v ≤ -5 m/s) vs. Crash (v > -5 m/s)
2. Impact velocity (m/s)
3. Fuel consumption (kg)
4. Descent time (s)
5. Control saturation levels (%)

**Output**: 6 plots showing impact of each emergency
- Landing success rates
- Impact velocity distributions
- Fuel efficiency comparison
- Velocity/altitude trajectories
- Control effort during failure

### Experiment 3: Interactive Controller Demos

**Purpose**: Educational visualization of control theory principles

#### PID Tuning Demo
```bash
python experiments/PID_presentation.py
```

**Features**:
- Interactive sliders for Kp, Ki, Kd adjustment
- Real-time control response visualization
- Click to set setpoint target
- "Capture Plots" button to record and analyze transient response
- Display of P/I/D term contributions

#### LQR Tuning Demo
```bash
python experiments/LQR_presentation.py
```

**Features**:
- Interactive tuning of Q (state cost) and R (control cost) matrices
- Real-time LQR gain recomputation
- Visualization of trade-off between state tracking and control effort
- "Capture Plots" button for transient analysis

---

## Installation & Setup

### Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk Space**: ~500MB for dependencies

### Dependencies

See `requirements.txt` for complete list. Key packages:

```
numpy>=2.3          # Numerical computing
scipy>=1.16         # Scientific computing (CARE solver)
matplotlib>=3.10    # Plotting and visualization
PyQt5>=5.15         # Desktop GUI
pyqtgraph>=0.13     # Real-time visualization
```

### Installation Steps

1. **Clone or extract the project**:
```bash
cd "Space Lander Simulator"
```

2. **Create a Python virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Verify installation**:
```bash
python -c "import numpy, scipy, PyQt5; print('All dependencies installed!')"
```

---

## Usage Guide

### Running the GUI Dashboard

Start the interactive dashboard application:

```bash
python app.py
```

**Dashboard Features**:
- **Simulation Panel**: Select planet, lander, controller, emergency scenario
- **Status Panel**: Real-time landing status (IDLE, DESCENDING, LANDED, CRASHED)
- **Radar Panel**: Top-down view with craft orientation ("TOP" indicator)
- **Telemetry Panel**: Real-time measurements (altitude, velocity, fuel, orientation)
- **3D Lander View**: 3D visualization of lander attitude
- **Engine Panel**: Per-engine throttle visualization
- **Emergency Log**: Real-time alerts and warning messages

**Usage**:
1. Select planet (Earth, Moon, Mars)
2. Select lander model (Falcon 9, Moon Lander)
3. Select control algorithm (PID, LQR, MPC)
4. Select emergency scenario (None or specific failure)
5. Click "Start" to begin simulation
6. Click "Stop" to reset

### Running Command-Line Simulator

For non-interactive, quick simulations:

```bash
python main.py
```

**Prompts**:
1. Select planet from available list
2. Simulation runs automatically using default controller
3. Outputs final landing status and telemetry

### Running Experiments

#### Controller Comparison
```bash
cd experiments
python controller_comparison_experiment.py
```

Generates comparison plots and statistics for all three controllers across Earth, Moon, Mars.

#### Emergency Robustness Analysis
```bash
cd experiments
python emergency_scenario_experiment.py
```

Tests MPC controller against all six emergency scenarios; generates impact analysis plots.

#### Interactive Tuning Demos
```bash
python PID_presentation.py      # PID tuning and visualization
python LQR_presentation.py      # LQR tuning and visualization
```

---

## Technical Documentation

### Configuration (core/config.py)

Global defaults for all controllers:

```python
PID_DEFAULTS = {
    'Kp': 8.0,
    'Ki': 1.5,
    'Kd': 3.0,
}

LQR_DEFAULTS = {
    'Q': np.diag([0.01, 200.0]),
    'R': np.array([[1.0]]),
}

MPC_DEFAULTS = {
    'N': 20,
    'Q': np.diag([10.0, 1.0]),
    'R': np.array([[0.1]]),
    'u_limits': (0.0, 1.0),
    'rate_limit': 0.5,
}
```

### Lander Models

#### Falcon 9
- **Engines**: 4 Merlin engines in grid configuration
- **Max thrust per engine**: ~700 kN
- **Dry mass**: ~25 metric tons
- **Fuel capacity**: ~111 metric tons
- **Dimensions**: ~12m × 3.7m

#### Moon Lander
- **Engines**: 2 descent engines
- **Configuration**: Customizable for specific mission profile
- **Use case**: Lunar landing analysis

### Adding Custom Controllers

1. Implement the `IController` interface:
```python
class MyController(IController):
    def update(self, measurement: float, dt: float, altitude: float = 0.0) -> float:
        # Return desired acceleration (m/s²)
        pass
    
    def reset(self):
        # Reset internal state
        pass
```

2. Register in `controller_factory.py`

3. Use in simulation via configuration

---

## Results & Conclusions

### Key Findings

#### Controller Performance Ranking

**For nominal (non-emergency) scenarios**:

1. **MPC**: 
   - Most consistent landing velocity (closest to target)
   - Highest fuel efficiency with constraints
   - Smooth, predictable control

2. **LQR**: 
   - Fast descent, good stability
   - May violate soft constraints
   - Sensitive to model mismatch

3. **PID**: 
   - Fastest response time
   - Acceptable performance with proper tuning
   - More difficult to tune for multi-planet operation

#### Emergency Robustness

- **Engine Failures**: All controllers can handle 1 engine loss; 2 failures likely fatal
- **Stuck Engine**: Control authority severely reduced; difficult even for MPC
- **Response Lag**: 
  - Mild (1s): Manageable with all controllers
  - Medium (2s): MPC maintains control; PID/LQR struggle
  - Severe (5s): All controllers likely to fail

#### Multi-Planetary Performance

- **Earth**: All controllers effective; MPC dominates
- **Moon** (low gravity): Response lag more critical; MPC recommended
- **Mars** (medium gravity): Controller selection less critical than on Moon

### Mission-Critical Recommendations

**For Nominal Operations**: 
- **Recommendation**: MPC
- **Rationale**: Best trajectory tracking, explicit constraint handling, robustness to disturbances

**For Emergency Resilience**: 
- **Recommendation**: MPC with LQR backup
- **Rationale**: MPC handles failures well; LQR provides fast response if MPC fails

**For Computational-Constrained Environments**: 
- **Recommendation**: PID with LQR supervision
- **Rationale**: PID is fast; LQR can detect and correct deviations

**Critical Failure Thresholds**:
- Response lag > 3s makes landing very difficult
- Multiple engine failures reduce safety margins significantly
- Fuel margin should be ≥ 15% for emergency maneuvers

---

## File Descriptions

| File | Purpose |
|------|---------|
| `core/Simulator.py` | Main simulation loop and state propagation |
| `core/PhysicsEngine.py` | Physics calculations (forces, torques, integration) |
| `core/ThrustAllocator.py` | Thrust distribution optimization |
| `core/ThrustManager.py` | Thrust command management and safety checks |
| `core/FuelManager.py` | Fuel consumption and depletion logic |
| `core/config.py` | Global configuration and factory functions |
| `core/controllers/*.py` | Control algorithm implementations |
| `core/emergencies/*.py` | Emergency scenario definitions and handling |
| `UI/dashboard_UI.py` | Main dashboard window and layout |
| `UI/panels/*.py` | Individual visualization panels |
| `experiments/*.py` | Research experiments and analysis scripts |
| `app.py` | Dashboard application entry point |
| `main.py` | Command-line simulator entry point |

---

## Author & Attribution

**Thesis**: Space Lander Simulator: Comparative Analysis of Control Algorithms in Virtual Planetary Environments

**Developed**: 2025

**Language**: Python 3.8+

**Libraries**: NumPy, SciPy, Matplotlib, PyQt5, pyqtgraph

---

## References

### Control Theory
- Boyd, S., El Ghaoui, L., Pérés, E., & Balakrishnan, V. (1994). *Linear Matrix Inequalities in System and Control Theory*. SIAM.
- Goodwin, G. C., Graebe, S. F., & Salgado, M. E. (2001). *Control System Design*. Prentice Hall.
- Åström, K. J., & Hägglund, T. (1995). *PID Controllers: Theory, Design, and Tuning*. Instrument Society of America.

### Spacecraft Dynamics
- Curtis, H. D. (2013). *Orbital Mechanics for Engineering Students* (3rd ed.). Butterworth-Heinemann.
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006). *Revisiting Spacetrack Report #3*.

### Model Predictive Control
- Camacho, E. F., & Bordons, C. (2007). *Model Predictive Control* (2nd ed.). Springer.
- Rawlings, J. B., Mayne, D. Q., & Diehl, M. M. (2017). *Model Predictive Control: Theory, Computation, and Design* (2nd ed.). Nob Hill Publishing.

---

## License

This project is provided for educational and thesis purposes.

---

## Contact & Support

For questions or technical support regarding this simulator, please refer to the thesis documentation or contact the thesis advisor.

**Last Updated**: February 2026
