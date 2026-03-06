# x-django-sandbox

A Django project with a custom user model, set up for building a REST API (login, register, account management).

## Stack

- **Python** 3.12+
- **Django** 6.x
- **uv** for dependency and environment management

## Project structure

- `config/` – Django project settings, URLs, WSGI/ASGI
- `accounts/` – Custom user model and auth-related logic (login, register, profile)
- `manage.py` – Django management script

## Setup

1. Clone the repo and enter the project directory.

2. Install dependencies and sync the environment:

   uv sync
   