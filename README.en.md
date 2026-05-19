# Python Togo API Version 2.1.0

Official API for Python Togo.
This project centralizes backend features and provides a shared base for platform evolution.

## Purpose

- Provide a stable and structured API with FastAPI
- Centralize project endpoints
- Make community contributions easier

## Contribution

### 1) Fork the project

Fork this repository, then clone your fork locally:

```bash
git clone https://github.com/<your-username>/pythontogo_api.git
cd pythontogo_api

```


### 1) Run with script (Linux/MacOS)
Make sure you have Docker installed and running on your machine.
```bash
# Copy the example file, then update variables

cp app/.env.example app/.env

# Linux/MacOS: Make the entrypoint script executable
chmod +x entrypoint.sh

# run script to start the API with Docker
./entrypoint.sh
```

## Or Develop Locally

### 2) Local Development


## 2.1)  Install dependencies and configure environment

```bash
pip install -r requirements.txt


# Copy the example file, then update variables

cp app/.env.example app/.env
```

### 2.2) Run migrations

```bash
python -m app.database.migrations

or 

python3 -m app.database.migrations
```

Check migration configuration in the project's Alembic files if needed.

### 2.3) Start the API in development

```bash
fastapi dev app/main.py --port 8001
```

You can replace 8001 with any available port.

## Version

This branch contains the new version of the project.

## Contribution Best Practices

- Create one branch per feature/fix
- Write clear commits
- Open a Pull Request with a precise description
- Add/update tests when needed
