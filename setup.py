from setuptools import setup, find_packages

setup(
    name='pyssm',
    version='0.4.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'boto3',
        'inquirer'
    ],
    entry_points={
        'console_scripts': [
            'pyssm=pyssm.start:main',
        ],
    },
    author="minhyeok.park",
    author_email="qkralsgur721@gmail.com",
    description="CLI for managing AWS ECS services interactively",
    keywords="AWS ECS CLI",
    url="https://github.com/Park-Seaweed/AWS-ECS-EC2-SSM-CLI.git",
    python_requires='>=3.6',  # Python 버전 요구 사항
)
