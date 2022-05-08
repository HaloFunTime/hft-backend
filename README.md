# hft-backend

The HaloFunTime Backend application is a Django API (using Django REST Framework) that connects to a PostgreSQL database.

NOTE: We are using Python 3.10 for development - it is entirely possible that a default installation of Python 2 exists on your machine (especially if you are using an older version of Mac OS X). All commands in this README that refer to calling the `python` executable are referring to Python 3.10, so make the appropriate changes to your local machine to ensure compatibility.

# Initial Setup

## Local dependencies

To run the application locally, you must have the following installed. We recommend using a package manager (like Homebrew on Mac OS X) to install each of the following:

* [Python](https://www.python.org/) (Version 3.10)
* [Docker](https://www.docker.com/) (should include Docker Compose)
* [git](https://git-scm.com/)
* [pre-commit](https://pre-commit.com/)

## Retrieve the code and seed the environment

1. Clone this repository locally with `git clone https://github.com/HaloFunTime/hft-backend.git`.
2. Copy the contents of the existing `.env.example` file into a new file called `.env` in the same directory. If sensitive values are needed for local development, they will be marked as `{PLACEHOLDER}` and you will need to ask an existing contributor to this repository for suitable test values to use in your `.env` file. Your local development flow will not work until all such `{PLACEHOLDER}` values are filled in with real values.

## Run the application for the first time

1. Run your local application for the first time by using `make` while inside the `/hft-backend` directory.
2. Run the default Django migrations against your local database by running `make migrate`.
3. Create a superuser for your local instance by using `make createsuperuser`.
   * For ease of use, use the same email address for both the **Username** and **Email** fields.
   * Use an easy-to-remember email address and a simple password like `password` since this is local and security isn't a priority.
4. Verify that `hft-backend` is running by visiting `http://localhost:8000` in a browser window (feel free to visit `http://localhost:8000/funpolice/` and sign in with your superuser credentials as well - that's the standard Django admin page).
5. Kill your local application by using `CONTROL+C` or the command `make kill`. You did it!

# Active Development Guidelines

Variables in all Python code should be named using the `snake_case` stylistic convention. The `black` autoformatter is configured to run prior to every commit, and will thus enforce a degree of stylistic uniformity.

## Application development workflow

* Start your local application by using `make` while inside the `/hft-backend` directory.
    * Django may warn you with something like `You have X unapplied migration(s)` - you can run `make migrate` to apply them.
* Make changes to `.py` files as needed
    * Saving changes to a Python file will hot-reload Django. You will know this has happened when you see `{filename here} changed, reloading` in the terminal in which you ran `make`.
* If you make a change to a `models.py` file, you will need to run `make migrations` to generate updated migration files - these will need to be included in your git commit so we can run them against the production database.
* **TODO:** Explain Postman API testing here
* Kill your local application when you're done developing by using `CONTROL+C` or the command `make kill`.

# Database Migrations

Any time a class in a `models.py` file is updated, the database must be updated to match the newly-defined model class. Django tracks these database updates by generating *migration* files which are then applied to the database to keep everything in sync. So there are two phases to migration - you must *generate* the migration files, and then *apply* the migration files to the database.

You are responsible for generating *migration* files if you change a class in a `models.py` file. There's a catch though - migration files can only be generated if a live version of the database is running, because the migration tool needs to diff against the existing database in order to figure out what has changed. Docker greatly simplifies this process.

## Django: Generate Migrations

Run `make migrations` once you've saved the changes to all `models.py` files you intend to change. This will create the *migration* files for all apps and subapps with detected changes, which you will want to include in your git commit.

## Django: Apply Migrations

Run `make migrate` once you've generated all migrations. This will take the *migration* files generated in the previous step and immediately apply them to your local database, which is running in the `postgres` container.
