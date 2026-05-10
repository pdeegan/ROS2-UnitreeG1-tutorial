from setuptools import find_packages, setup

package_name = "g1_speech"

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
    description="Lesson 08 — speech I/O.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "listen = g1_speech.listen:main",
            "speak = g1_speech.speak:main",
        ],
    },
)
