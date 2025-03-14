from setuptools import setup, find_packages

setup(
    name="meterinstall-api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "sqlalchemy==2.0.23",
        "alembic==1.12.1",
        "python-dotenv==1.0.0",
        "pydantic==2.4.2",
        "pydantic-settings==2.0.3",
        "psycopg2-binary==2.9.9",
        "asyncpg==0.28.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.6",
        "email-validator==2.1.0",
        "httpx==0.25.1",
        "pandas==2.1.2",
        "requests==2.31.0",
        "aiohttp==3.8.6",
    ],
    description="Meter Installation Tracking System API",
    author="PWA",
    author_email="admin@pwa.co.th",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.9",
) 