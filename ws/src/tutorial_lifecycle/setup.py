from setuptools import find_packages, setup

package_name = "tutorial_lifecycle"

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
    description="Lesson 05 — lifecycle node.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "lifecycle_talker = tutorial_lifecycle.lifecycle_talker:main",
        ],
    },
)
