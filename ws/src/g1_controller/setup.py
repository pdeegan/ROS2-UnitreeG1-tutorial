from setuptools import find_packages, setup

package_name = "g1_controller"

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
    description="Lesson 09 — high-level G1 controller.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "demo = g1_controller.demo:main",
            "wave_client = g1_controller.wave_client:main",
        ],
    },
)
