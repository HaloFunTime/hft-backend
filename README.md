# hft-backend
Welcome to the HaloFunTime backend repo, a [Django](https://www.djangoproject.com/) project that manages resources needed for other HaloFunTime services, primarily a [Django REST Framework](https://www.django-rest-framework.org/) API that is OpenAPI/Swagger ready via `drf-spectacular` (with full endpoint documentation accessible on the `/docs` route).

This codebase is designed to be deployed to https://fly.io for production use at [https://api.halofuntime.com] and run locally with Docker Compose for development purposes, with as much code shared between both modalities as possible.

# Initial Setup

## Local Dependencies

To run the application locally, you must have the following installed. It is recommended to use a package manager (like Homebrew on Mac OS X) to install each of the following:

* [Python](https://www.python.org/) (3.10.X, - should include Pip)
   * macOS: `brew install python@3.10`
* [Docker](https://www.docker.com/) (should include Docker Compose)
   * macOS: `brew install docker`
* [pre-commit](https://pre-commit.com/)
   * macOS: `brew install pre-commit`

## Local Setup

1. Clone this repository locally with `git clone https://github.com/HaloFunTime/hft-backend.git`
1. Create a local `.env` by running the command `cp .env.example .env` (and then adding actual values to the variables in the `.env` file as needed)
1. For ease of use, make all `dev-`-prefixed shell scripts directly executable by issuing the following shell command: `find dev-*.sh | xargs chmod +x`

## First-time run Setup

1. Run your local application for the first time by running the script `./dev-start.sh`
1. Create a superuser for your local instance with `./dev-manage.sh createsuperuser` and follow the interactive instructions
   * Use your Xbox gamertag for `Username` and any email you have access to for `Email`
   * It's easiest to use a simple password like `password` since this is local and thus safe
1. Verify that the server is running by visiting `http://localhost:8000` in a browser window (feel free to visit `http://localhost:8000/staff/` and sign in with your superuser credentials as well - that's the standard Django admin page)
1. Kill your local application by either using CTRL+C in the shell in which it's running, or by running the script `./dev-stop.sh`

Docker is configured to build two containers - one running the Django web server (called `hftbackend` in the logs) and one running the PostgreSQL database instance that Django uses to store and read data (called `hftdata` in the logs). Further setup specifics can be viewed in the `docker-compose.yml` file.

# Active Development Guidelines

## Quickstart

1. Start your local application with `./dev-start.sh` (verify that it is running by opening [http://localhost:8000] in a browser)
1. Make changes to Python files as needed (saving changes to Python files will hot-reload your running application)
   * Create new apps with `./dev-newapp APPNAME`
   * Run tests:
      * Run all tests by **not** providing app names (IE `./dev-tests.sh`)
      * Run tests for **specific** apps by providing appnames (IE `./dev-tests.sh APP1 APP2 APP3`)
   * Run `./dev-format.sh` to reformat files to comply with our formatters
   * Run Django `manage.py` commands with `./dev-manage.sh`
      * Generate database migration files with `./dev-manage.sh makemigrations`
1. Stop your dev application with `./dev-stop.sh` when you are done
1. Bundle your changes into git commits on a branch not named `main`, and push your branch to the origin repository
1. Open a pull request from your branch targeting the `main` branch (tests should automatically run - if they fail, update your branch until the tests are working)

## Stylistic Conventions

Variables and function declarations in Python code are to be named using the `snake_case` convention. Database tables created by our code should be named in `PascalCase` to explicitly differentiate them from tables created by Django.

## Development Scripts

Use `dev-start.sh` and `dev-stop.sh` to start and stop the application locally. Note that `dev-manage.sh`, `dev-newapp.sh`, and `dev-test.sh` each require that the application be running.

* `dev-format.sh`: Auto-formats all files in the codebase
* `dev-manage.sh`: Passes a `manage.py` command to the application instance running inside the Docker container
   * **NOTE:** The app must be running via Docker Compose for this to succeed
   * **EXAMPLE:** `./dev-manage.sh makemigrations`
* `dev-newapp.sh`: Creates a new app in the `/apps` directory
   * **NOTE:** The app must be running via Docker Compose for this to succeed
* `dev-start.sh`: Runs the application via Docker Compose
* `dev-stop.sh`: Stops the application via Docker Compose
* `dev-tests.sh`: Runs tests for apps in the `/apps` directory
   * **NOTE:** The app must be running via Docker Compose for this to succeed

## Directory Structure

We are utilizing a slightly non-standard structure for this Django project. Our main Django settings are contained in a "special" app called `config` that lives underneath the project root (which contains shared abstract models in `models.py`, the primary `settings.py` and `urls.py` files, and ASGI/WSGI configs).

All other Django apps are contained in `/apps`. Deployment/release scripts are contained in `/scripts`, static files are contained in `/static`, and templates are contained in `/templates`.

> NOTE: NEW DJANGO APPS SHOULD **ONLY** BE CREATED WITHIN THE `apps` FOLDER USING THE `dev-newapp.sh` script.

## Apps

By convention we define all new Django apps inside the `apps` directory. For the most part, each app should contain a logical unit of functionality - for example, all code related to calling the Halo Infinite API is contained in the `/halo_infinite_api` app, and all code related to generating map and gametype series is contained in the `/series` app. Cross-app dependencies may exist, but should be limited where possible.

New apps can be created inside the `apps` folder by running the `./dev-newapp.sh` script with an app name - IE `./dev-newapp.sh example` will create placeholder files for the new app in `/apps/example`.

Apps will usually contain some sampling of the following files:

* `__init__.py` - loads any AppConfig specified in `apps.py`
* `admin.py` - makes the model defined in the app visible in the Staff portal; configures specifics relating to that visibility
* `apps.py` - stores metadata for an application (usually only useful for specifying filepath overrides in the event that there is a namespacing issue)
* `models.py` - defines database tables, fields, and corresponding data types
* `serializers.py` - defines Django REST Framework serializers
* `tests.py` - defines test cases for the app
* `views.py` - defines custom views - functions that take HTTP requests in and return HTTP responses

## Database Migrations

Any time a class in a `models.py` file is updated, the database must be updated to match the newly-defined model class. Django tracks these database updates by generating *migration* files which are then applied to the database to keep everything in sync. There are two phases to migration - you must *generate* the migration files, and then *apply* the migration files to the database.

You are responsible for generating *migration* files if you change a class in a `models.py` file. There's a catch though - migration files can only be generated if a live version of the database is running, because the migration tool needs to diff against the existing database in order to figure out what has changed. Docker greatly simplifies this process.

### Generating Migrations

Run `./dev-manage.sh makemigrations` once you've saved changes to all the `models.py` files you intend to change. This command will create the *migration* files for all apps with detected changes, which you will want to include in your git commit.

### Applying Migrations

Migrations are applied automatically on application startup in our Docker Compose config, but you can manually apply migrations without restarting your local application by running `./dev-manage.sh migrate`. Either process will take the *migration* files generated in the previous step and immediately apply them to the database, which is running in the `hftdata` container.

## DevX Notes

Several quality-of-life features are baked in via this repository's `pre-commit` config, including elimination of trailing whitespace, EOF auto-add, YAML formatting, Python syntax updating with `pyupgrade`, Python autoformatting with `black`, Python import ordering with `isort`, and PEP8 compliance with `flake8`.

Most development scripts exist to simplify the dev flow for newer developers; for those contributors who are more experienced, feel free to manually execute commands within Docker containers and break the "rules" as appropriate (IE with `noqa` comments). It is our explicit goal that this project be very approachable for new developers, so please default to simplicity when possible.
