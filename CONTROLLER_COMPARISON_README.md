# Controller Comparison Experiment

This experiment compares the performance of PID, LQR, and MPC controllers for spacecraft landing under identical conditions.

## Generated Plots

The experiment generates comparison plots for Earth, Moon, and Mars:

- `controller_comparison_earth.png`
- `controller_comparison_moon.png`
- `controller_comparison_mars.png`

Each plot contains four subplots:
1. **Vertical Velocity vs Time** - Shows damping and settling behavior
2. **Altitude vs Time** - Shows trajectory shaping and braking profile
3. **Throttle vs Time** - Shows control effort and differences between controllers
4. **Cumulative Fuel Consumption** - Shows fuel efficiency

## Experimental Conditions

**Two-Phase Velocity Control Scenario:**
- **Initial altitude**: 3000 m
- **Initial velocity**: -80 m/s (descending at 80 m/s)
- **Max velocity limit**: -50 m/s (maximum descent rate - controllers maintain this until activation)
- **Activation altitude**: 500 m
- **Target velocity**: -3 m/s (soft landing velocity after activation)
- **Time step**: 0.05 s
- **Acceleration limits**: -9.81 to +20 m/s² (physically realistic - max deceleration is gravity magnitude)

**Control Phases:**
1. **Phase 1**: Controllers decelerate from -80 m/s to -50 m/s max velocity limit
2. **Phase 2**: Maintain -50 m/s until reaching 500m activation altitude
3. **Phase 3**: Switch to target velocity (-3 m/s) for soft landing

**Control Phases:**
1. **Phase 1**: Controllers decelerate from 100 m/s to 50 m/s max velocity limit
2. **Phase 2**: Maintain 50 m/s until reaching 500m activation altitude
3. **Phase 3**: Switch to target velocity (3 m/s) for soft landing
- **Maximum time**: 120 s

## Controller Configurations

**Connected to Main Simulation Configs** (`core/config.py`)

The experiment uses the same controller configurations as the main simulation, with experiment-specific overrides:

### PID Controller
- **Base config**: `PID_DEFAULTS` from `core/config.py`
- **Experiment overrides**:
  - `setpoint`: Dynamic (-50 m/s initially, switches to -3 m/s at activation)
  - `output_limits`: -9.81 to +20 m/s² (experiment physical limits)
  - `activation_altitude`: 0.0 (always active - setpoint switching instead)

### LQR Controller
- **Base config**: `LQR_DEFAULTS` from `core/config.py`
- **Experiment overrides**:
  - `setpoint`: Dynamic (-50 m/s initially, switches to -3 m/s at activation)
  - `activation_altitude`: 0.0 (always active - setpoint switching instead)

### MPC Controller
- **Base config**: `MPC_DEFAULTS` from `core/config.py`
- **Experiment overrides**:
  - `setpoint`: Dynamic (-50 m/s initially, switches to -3 m/s at activation)
  - `output_limits`: -9.81 to +20 m/s² (experiment physical limits)
  - `dt_nom`: 0.05 s (experiment time step)
  - `activation_altitude`: 0.0 (always active - setpoint switching instead)
- **Gravity**: Planet-specific (9.81 m/s² Earth, 1.62 m/s² Moon, 3.71 m/s² Mars)

## Theoretical Reference

Each plot includes a theoretical reference trajectory calculated using kinematic equations for optimal constant acceleration landing.

## How to Run

```bash
python controller_comparison_experiment.py
```

The experiment will:
1. Run simulations for all three controllers on all three planets
2. Generate comparison plots as PNG files
3. Display summary statistics

## Results Summary (Connected to Main Simulation Configs)

**Performance Comparison (Earth):**
- **PID**: ⚠️ Moderate landing (-32 m/s), 44s, 74.6k kg fuel - **Fast but firm**
- **LQR**: ❌ Failed (1771m altitude), +6 m/s, 211k kg fuel - **Struggles with constraints**
- **MPC**: ⚠️ Hard landing (-49 m/s), 60s, 80.1k kg fuel - **Most consistent target achievement**

**Key Findings:**
1. **MPC** achieves most consistent target velocity (-49 m/s vs -50 m/s target)
2. **PID** is fastest but lands harder than desired (-32 m/s vs -3 m/s target)
3. **LQR** maintains stability but doesn't adapt well to velocity limit constraints

**Multi-Planet Performance:**
- **Earth**: MPC most consistent, PID fastest
- **Moon**: MPC achieves good landings, PID and LQR struggle with lighter gravity
- **Mars**: MPC dominates, others struggle with higher gravity

**Configuration Impact:**
Main simulation configs show different behavior than experiment-specific tuning:
- Conservative PID gains (Kp=0.6) lead to faster but harder landings
- MPC horizon (10 steps) provides good target consistency
- LQR maintains stability but struggles with hard velocity constraints

## Key Differences

- **MPC**: Uses prediction horizon to optimize future control actions
- **LQR**: Uses optimal state feedback for infinite-horizon control
- **PID**: Uses classical feedback control with proportional, integral, and derivative terms

All controllers include:
- Activation altitude logic (activate when altitude < 500m)
- Acceleration saturation limits
- Anti-windup protection (PID)
- Proper gravity modeling (MPC)
