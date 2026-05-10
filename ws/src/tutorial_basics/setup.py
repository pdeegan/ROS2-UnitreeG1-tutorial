from setuptools import find_packages, setup

package_name = "tutorial_basics"

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
    description="Lesson 01 — minimal rclpy node.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "hello = tutorial_basics.hello:main",
        ],
    },
)
