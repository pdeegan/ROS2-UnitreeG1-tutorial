# Command for a single motor (joint).
uint8   mode    # 0=damping, 1=position, 2=velocity, 3=torque
float32 q       # target angle (rad), used in position mode
float32 dq      # target velocity (rad/s), used in velocity mode
float32 tau     # feed-forward torque (N*m)
float32 kp      # position gain
float32 kd      # damping gain
