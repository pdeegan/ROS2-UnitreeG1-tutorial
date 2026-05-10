# Connecting to a Unitree G1

How the G1 looks from a developer's terminal, the safety contract,
and the network plumbing you need before lesson 07 will see the
robot.

## What the G1 exposes

The G1 runs an onboard controller that publishes / subscribes to a
small set of DDS topics over CycloneDDS on the wired ethernet
interface. The two that matter most for the tutorial:

| DDS topic | IDL type | Direction | Rate |
|---|---|---|---|
| `rt/lowstate` | `unitree_hg.msg.LowState_` | from robot | ~500 Hz |
| `rt/lowcmd` | `unitree_hg.msg.LowCmd_` | to robot | up to 500 Hz |
| `rt/sportmode/state` | `unitree_hg.msg.SportModeState_` | from robot | 50 Hz |
| `rt/api/sport/request` | `unitree_api.msg.Request_` | to robot | on demand |

`LowState_` carries 29 motor states (legs + arms + waist + neck),
the IMU, the battery, and a wireless remote echo. `LowCmd_` is the
companion command: 29 per-motor entries with mode + position +
velocity + feed-forward torque + Kp/Kd gains.

## Network topology

Out of the box, the G1's wired ethernet expects to be on
**192.168.123.0/24**. The robot is typically `192.168.123.161` (the
high-level board) and `192.168.123.99` (the low-level board), but
the IDs vary by firmware revision — confirm with
`ros2 service call /rt/sportmode/get_status` once you're connected.

Your host needs a NIC with a static IP on that subnet. On WSL2 this
means **mirrored networking** is required:

```ini
# ~/.wslconfig on the Windows host
[wsl2]
networkingMode=mirrored
```

`wsl --shutdown` from PowerShell, reopen the shell, and verify with
`ip -br addr` — you should now see the same interfaces as `ipconfig`
shows on Windows.

Then tell CycloneDDS which interface to use:

```xml
<NetworkInterface autodetermine="false" name="eth0" priority="default" multicast="default" />
```

…in `install/cyclonedds.xml`. Replace `eth0` with the actual name
from `ip -br addr` (often `eth0` or `Ethernet`).

Finally:

```bash
export CYCLONEDDS_URI=file://$REPO/install/cyclonedds.xml
```

## Bring-up checklist

In order, before any motion lesson:

1. **Hoist the robot or enable damping mode.** The G1 does not
   self-balance until `STAND` mode is requested *and* the controller
   has converged. If you skip this, it falls.
2. **Confirm the wired ethernet link.** `ip -br addr` shows the
   192.168.123.x interface; `ping 192.168.123.161` returns replies.
3. **Set the CycloneDDS URI** as above.
4. **Run `ros2 topic list` after bringup.** You should see
   `rt/lowstate` and `rt/sportmode/state` listed. If not, your
   interface or multicast config is wrong — see
   [docs/troubleshooting.md](troubleshooting.md).
5. **Start the bridge and safety latch.**
   ```bash
   ros2 run g1_bridge bridge &
   ros2 run g1_bridge safety &
   ```
6. **Verify state flow.**
   ```bash
   ros2 topic hz /g1/lowstate     # should be 50 Hz or higher
   ros2 topic echo /g1/imu --once
   ```
7. **Only then** consider engaging safety.

## Safety contract

The tutorial enforces two layers of safety. Do not patch around
them.

- **Layer 1 — bridge.** `g1_bridge.bridge` refuses to forward
  `/g1/lowcmd` to the SDK unless `/g1/safety_engaged` is True.
- **Layer 2 — controller.** `g1_controller.demo` refuses to publish
  `/g1/lowcmd` unless `/g1/safety_engaged` is True.

Both layers subscribe to the latch with `transient_local` durability
so a node that joins late still sees the current value.

Engaging the latch:

```bash
ros2 service call /g1/safety/engage std_srvs/srv/Trigger
```

Releasing it:

```bash
ros2 service call /g1/safety/release std_srvs/srv/Trigger
```

Engaging the latch does **not** start motion. It only stops the
bridge from dropping commands. Motion still requires either a
service call to `g1_controller`'s `/g1/set_mode` or a stream of
manually-crafted `/g1/lowcmd` messages.

## Failure modes (and what to do)

- **Bridge says "dropped /g1/lowcmd — safety disengaged".** The
  latch is the gate; this is working as designed. Engage with the
  service call above.
- **`ros2 topic hz /g1/lowstate` shows 0 Hz.** No DDS traffic is
  reaching the bridge. Likely causes: wrong interface in
  `cyclonedds.xml`, no IP on 192.168.123.x, multicast blocked on
  the interface.
- **Bridge crashes at startup with "ChannelFactoryInitialize fail".**
  The SDK can't bind the interface name you passed. Check
  `ip link show <name>`.
- **G1 falls when you call STAND.** It wasn't hoisted, or you gave
  it `STAND_UP` from `SIT` without the prerequisite ramp. See the
  G1 Operations Manual §4.3.
- **Battery dropping fast under no motion.** A G1 in `STAND` mode
  burns ~150 W just keeping balance. `DAMP` (mode 0) is the safe
  parking state when not actively using the robot.

## Pedagogical scope, not production stack

The tutorial's G1 packages teach the shape of an integration —
state flowing in, commands flowing out, a safety latch in the
middle. A production stack adds:

- Gain ramping (smoothstep entry / exit on every motion).
- Watchdog with hard-fail to damping after stale-state timeouts.
- CRC validation on inbound LowState.
- Mode-machine cross-check before publishing LowCmd.
- Sportmode API for high-level behaviors (the tutorial uses
  LowCmd-only paths for clarity).

These are good follow-up exercises, not omissions to apologize for.
