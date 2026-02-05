# Coordinate Systems in Space Lander Simulator

This document defines all coordinate systems used in the Space Lander Simulator, ensuring unambiguous interpretation of position, velocity, orientation, and forces.

## Inertial Reference Frame

The inertial reference frame is a fixed Cartesian coordinate system used for global position and velocity tracking.

### Definition
- **Type**: Right-handed Cartesian coordinate system
- **Origin**: Located at the planetary surface landing reference point (altitude = 0)
- **Fixed**: Non-rotating with respect to the planetary body

### Axes
- **X-axis**: Horizontal direction (positive eastward)
- **Y-axis**: Vertical direction (positive upward)
- **Z-axis**: Horizontal direction perpendicular to X-axis (positive northward)

### Vector Representations
- **Position**: `position = [x, y, z]` where `y` is altitude above surface
- **Velocity**: `velocity = [vx, vy, vz]` where `vy` is vertical velocity
- **Acceleration**: `acceleration = [ax, ay, az]` where `ay` includes gravity effects

### Assumptions
- Non-rotating planetary body (no Coriolis effects)
- Flat planetary surface approximation
- Constant gravity magnitude (altitude-dependent for some planets)

## Body-Fixed Reference Frame

The body-fixed reference frame is attached to the lander and moves with it.

### Definition
- **Type**: Right-handed Cartesian coordinate system
- **Origin**: Located at the lander's center of mass
- **Moving**: Translates and rotates with the lander

### Axes
- **X-axis**: Aligned with lander's lateral geometry (positive rightward when facing forward)
- **Y-axis**: Aligned with lander's vertical geometry (positive upward through main body)
- **Z-axis**: Aligned with lander's longitudinal geometry (positive forward)

### Vector Representations
- **Engine Positions**: `engine_position = [px, py, pz]` relative to center of mass
- **Engine Directions**: `engine_direction = [dx, dy, dz]` unit vectors in body frame
- **Forces**: Applied at engine positions in body-fixed coordinates

### Usage
- Engine mount positions and thrust directions are defined in this frame
- Torque calculations use cross products with body-fixed vectors
- Thrust allocation solves for engine throttles in body coordinates

## Transformation Between Frames

Coordinate transformations convert vectors between inertial and body-fixed frames.

### Rotation Matrix
The lander's orientation is represented by Euler angles `orientation = [roll, pitch, yaw]` (radians).

The rotation matrix `R` transforms vectors from body-fixed to inertial frame:

```
R = R_z(yaw) * R_y(pitch) * R_x(roll)
```

Where:
- `R_x(roll)` rotates about X-axis
- `R_y(pitch)` rotates about Y-axis
- `R_z(yaw)` rotates about Z-axis

### Transformation Equations

**Body to Inertial**:
```
vector_inertial = R * vector_body
```

**Inertial to Body**:
```
vector_body = R^T * vector_inertial
```

Where `R^T` is the transpose (inverse for rotation matrices).

### Thrust Vector Transformation
Thrust forces are calculated in the body frame and transformed to inertial frame:

```
thrust_inertial = R * thrust_body
```

Where `thrust_body` is the sum of individual engine thrusts in body coordinates.

## Force and Torque Application

### Forces
- **Gravity**: Applied in inertial frame as `[0, -m*g, 0]`
- **Thrust**: Calculated in body frame, transformed to inertial frame
- **Drag**: Applied in inertial frame as function of relative velocity

### Torques
- **Thrust-induced torque**: `torque = Σ(r_i × F_i)` where `r_i` and `F_i` are in body frame
- **Aerodynamic torque**: Simplified as `torque = r × drag_force`

## Assumptions

### Motion Assumptions
- **Planar motion**: Primary motion occurs in X-Y plane (Z components small)
- **Rigid body**: Lander treated as rigid body with fixed mass distribution
- **Flat surface**: Planetary surface approximated as infinite flat plane

### Physical Assumptions
- **Point mass gravity**: Gravity acts at center of mass only
- **No planetary rotation**: No Coriolis or centrifugal forces
- **Simplified aerodynamics**: Drag proportional to velocity squared

### Computational Assumptions
- **Euler integration**: State derivatives integrated using forward Euler method
- **Instantaneous thrust**: Thrust forces applied instantaneously (no lag)
- **Linear drag**: Drag force linear with dynamic pressure

## Implementation Notes

### Vector Conventions
- All vectors are NumPy arrays of shape `(3,)` or `(n, 3)`
- Units: meters (m), meters/second (m/s), meters/second² (m/s²), radians (rad)
- Coordinate transformations use matrix multiplication: `result = R @ vector`

### Key Classes and Methods
- **Simulator**: Manages inertial frame state (`position`, `velocity`)
- **PhysicsEngine**: Applies forces in inertial frame
- **ThrustAllocator**: Solves thrust allocation in body frame
- **Engine**: Defines thrust direction and position in body frame

### Data Flow
1. Controller computes desired acceleration in inertial frame
2. ThrustAllocator converts to body frame thrust requirements
3. Engine throttles set based on body frame calculations
4. PhysicsEngine applies all forces in inertial frame

This coordinate system definition ensures consistent and unambiguous interpretation of all simulator quantities across different components and control algorithms.
