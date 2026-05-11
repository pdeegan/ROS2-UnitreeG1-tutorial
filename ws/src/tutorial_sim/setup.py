import os

from setuptools import find_packages, setup

package_name = "tutorial_sim"


def _data_files() -> list:
    files = [
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ]
    for sub in ("launch", "rviz", "config"):
        if not os.path.isdir(sub):
            continue
        items = [os.path.join(sub, f) for f in os.listdir(sub)
                 if os.path.isfile(os.path.join(sub, f))]
        if items:
            files.append((f"share/{package_name}/{sub}", items))
    return files


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=_data_files(),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ROS Tutorial",
    maintainer_email="tutorial@example.com",
    description="Lesson 06b — simulated humanoid in rviz2.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "animator = tutorial_sim.animator:main",
            "twist_listener = tutorial_sim.twist_listener:main",
        ],
    },
)
