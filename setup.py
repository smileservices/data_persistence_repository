from setuptools import setup, find_packages

setup(
    name="data_persistence_repository",
    version="0.1.1",
    author="vladimir gorea",
    author_email="vladimir@smileservices.dev",
    description="A repository implementation for data persistence.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/smileservices/data_persistence_repository",
    packages=find_packages(),
    install_requires=[
        "exceptiongroup==1.2.0",
        "greenlet==3.0.2",
        "iniconfig==2.0.0",
        "packaging==23.2",
        "pluggy",
        "psycopg2==2.9.9",
        "pytest==7.4.3",
        "SQLAlchemy==2.0.23",
        "SQLAlchemy-Utils==0.41.1",
        "tomli==2.0.1",
        "typing_extensions==4.9.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
