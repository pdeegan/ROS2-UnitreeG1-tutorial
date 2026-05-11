"""Launch the *real* Unitree G1 URDF (vendored via install/06_fetch_g1_assets.sh)
in rviz2, driven by joint_animator.

Usage::

    bash install/06_fetch_g1_assets.sh        # one-time, ~150 MB download
    bash scripts/ros2_build.sh g1_description
    ros2 launch tutorial_sim g1_sim.launch.py
    ros2 launch tutorial_sim g1_sim.launch.py rviz:=false
    ros2 launch tutorial_sim g1_sim.launch.py urdf:=g1_29dof_lock_waist.urdf

The animator publishes all 29 G1 joints. Each pattern (wave / walk /
squat / tpose / stretch / zero) sets a subset of joints from a small
analytic function; unset joints stay at 0.0. That's the simplest way
to animate a real URDF without a full IK / motion library.
"""

from __future__ import annotations

import os
import re

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _rewrite_mesh_paths(urdf_xml: str, pkg_name: str = "g1_description") -> str:
    """Convert relative `meshes/foo.STL` refs to `package://<pkg>/meshes/foo.STL`.

    The upstream Unitree G1 URDF uses relative paths like
    `<mesh filename="meshes/pelvis.STL"/>`. rviz2 cannot resolve those
    — without a package:// URI it has no way to find the mesh on disk,
    so the robot model renders as bare TF axes only.

    This rewrite makes the URDF self-contained for any consumer
    (rviz2, MoveIt, Gazebo) that resolves package:// via ament.
    """
    # Match filename="..." not already starting with /, package://, file://, or http
    pattern = re.compile(r'(<mesh\s+filename=")(?!/|package://|file://|https?://)([^"]+)(")')
    return pattern.sub(rf'\1package://{pkg_name}/\2\3', urdf_xml)


def _bringup(context, *args, **kwargs):
    g1_share = get_package_share_directory("g1_description")
    sim_share = get_package_share_directory("tutorial_sim")
    urdf_name = LaunchConfiguration("urdf").perform(context)
    rviz_name = LaunchConfiguration("rviz_config").perform(context)

    # Upstream layout puts URDFs at the top of g1_description/, but some
    # forks nest them under urdf/ — check both.
    candidates = [
        os.path.join(g1_share, urdf_name),
        os.path.join(g1_share, "urdf", urdf_name),
    ]
    urdf_path = next((p for p in candidates if os.path.isfile(p)), None)
    if urdf_path is None:
        available = [f for f in sorted(os.listdir(g1_share)) if f.endswith(".urdf")]
        raise FileNotFoundError(
            f"URDF '{urdf_name}' not found under {g1_share} or {g1_share}/urdf/.\n"
            f"  available: {', '.join(available) if available else '(none)'}"
        )

    with open(urdf_path) as f:
        urdf_xml = _rewrite_mesh_paths(f.read())

    rviz_path = os.path.join(sim_share, "rviz", rviz_name)

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": ParameterValue(urdf_xml, value_type=str)}],
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

    return [rsp, animator, rviz]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "urdf", default_value="g1_29dof.urdf",
            description="URDF file under share/g1_description/urdf/ to load",
        ),
        DeclareLaunchArgument(
            "pattern", default_value="wave",
            description="Animation pattern: wave | walk | squat | tpose | stretch | zero",
        ),
        DeclareLaunchArgument(
            "rviz", default_value="true",
            description="Bring up rviz2",
        ),
        DeclareLaunchArgument(
            "rviz_config", default_value="g1.rviz",
            description="rviz config file under share/tutorial_sim/rviz/",
        ),
        OpaqueFunction(function=_bringup),
    ])
