"""g1_bridge — lesson 07.

Bridge between unitree_sdk2py (CycloneDDS to the G1) and ROS 2.

Public modules
--------------
``bridge``  — main entry, ``ros2 run g1_bridge bridge``
``safety``  — safety latch node, ``ros2 run g1_bridge safety``
``sdk``     — thin wrapper over unitree_sdk2py with a fake-mode for dev
"""
