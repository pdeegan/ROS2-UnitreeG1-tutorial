"""Launch the full simulated humanoid: URDF + state publisher + animator + rviz2.

Usage::

    ros2 launch tutorial_sim sim.launch.py
    ros2 launch tutorial_sim sim.launch.py pattern:=walk    # different motion
    ros2 launch tutorial_sim sim.launch.py rviz:=false      # headless

What this brings up
-------------------
* ``robot_state_publisher`` — reads the URDF and republishes each link's
  transform on the TF tree given the current /joint_states.
* ``joint_animator`` — publishes /joint_states at 30 Hz with the chosen
  pattern (``wave``, ``walk``, or ``zero``).
* ``rviz2`` — preconfigured to show the RobotModel + TF + the world grid.

Run it once, then in a separate shell explore the live system::

    ros2 topic list
    ros2 topic echo /joint_states
    ros2 run tf2_ros tf2_echo base_link left_forearm_link
    ros2 param set /joint_animator pattern walk
"""

from __future__ import annotations

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    pkg_share = get_package_share_directory("tutorial_sim")
    xacro_path = os.path.join(pkg_share, "urdf", "humanoid.urdf.xacro")
    rviz_path = os.path.join(pkg_share, "rviz", "humanoid.rviz")

    pattern_arg = DeclareLaunchArgument(
        "pattern", default_value="wave",
        description="Animation pattern: wave | walk | zero",
    )
    rviz_arg = DeclareLaunchArgument(
        "rviz", default_value="true",
        description="Bring up rviz2 with the preset config",
    )

    robot_description = ParameterValue(
        Command(["xacro ", xacro_path]),
        value_type=str,
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
    )

    animator = Node(
        package="tutorial_sim",
        executable="animator",
        name="joint_animator",
        output="screen",
        parameters=[{"pattern": LaunchConfiguration("pattern")}],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_path],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return LaunchDescription([pattern_arg, rviz_arg, rsp, animator, rviz])
