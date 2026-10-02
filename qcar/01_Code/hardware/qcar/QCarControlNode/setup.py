from setuptools import find_packages, setup

package_name = 'QCarControlNode'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='brtdev',
    maintainer_email='brtdevkit@gmail.com',
    description='Control node for QCar using SMC and NMPC controllers.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # Formato: 'nombre_ejecutable = nombre_paquete.nombre_archivo:funcion_main'
            'node = QCarControlNode.node:main',
        ],
    },
)