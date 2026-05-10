# State of a single motor (joint) on the humanoid.
uint8 mode          # operating mode (0=damping, 1=position, 2=velocity, 3=torque)
float32 q           # joint angle (rad)
float32 dq          # joint velocity (rad/s)
float32 ddq         # joint acceleration (rad/s^2)
float32 tau_est     # estimated torque (N*m)
float32 temperature # motor temperature (C)
float32 vol         # motor voltage (V)
uint8   sensor_id   # internal sensor identifier
