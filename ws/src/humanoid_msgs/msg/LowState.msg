# Full low-level robot state, snapshot at the SDK tick rate (~500 Hz on G1).
std_msgs/Header header
uint32 tick                # SDK monotonic tick counter
uint8  mode_pr             # PR mode (0=pelvis-roll, 1=fixed-ankle-pitch)
uint8  mode_machine        # robot machine type id
sensor_msgs/Imu imu        # filled from imu_state (orientation+ang_vel+lin_acc)
humanoid_msgs/MotorState[] motor_state
float32 battery_voltage    # main battery voltage (V)
float32 battery_current    # main battery current (A)
