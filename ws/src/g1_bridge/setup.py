from setuptools import find_packages, setup

package_name = "g1_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ROS Tutorial",
    maintainer_email="tutorial@example.com",
    description="Lesson 07 — Unitree G1 DDS <-> ROS 2 bridge.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "bridge = g1_bridge.bridge:main",
            "safety = g1_bridge.safety:main",
        ],
    },
)
