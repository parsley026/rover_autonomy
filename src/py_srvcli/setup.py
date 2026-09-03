import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'py_srvcli'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
        package_name: ['metadata/*.csv'],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools', 'tutorial_interfaces'],
    zip_safe=True,
    maintainer='rex',
    maintainer_email='rex@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        'service = py_srvcli.service_member_function:main',
        'client = py_srvcli.client_member_function:main',
        'aruco_server = py_srvcli.aruco_server:main',
        'aruco_node = py_srvcli.aruco_node:main',
        'camera_node = py_srvcli.camera_node:main',
        ],
    },
)
