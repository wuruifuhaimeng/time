from setuptools import setup, find_packages

setup(
    name='time-tracker',
    version='1.0.0',
    description='时间记录与任务管理工具',
    author='你的名字',
    packages=find_packages(),
    install_requires=[
        'Pillow',
        'transformers',
    ],
    entry_points={
        'console_scripts': [
            'time-tracker=time_tracker.run:main',
        ],
    },
    python_requires='>=3.8',
    include_package_data=True,
    zip_safe=False,
) 