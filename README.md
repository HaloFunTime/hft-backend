# hft-backend

The HaloFunTime Backend application is a Django API (using Django REST Framework) that connects to a PostgreSQL database.

NOTE: We are using Python 3.10 for development - it is entirely possible that a default installation of Python 2 exists on your machine (especially if you are using an older version of Mac OS X). All commands in this README that refer to calling the `python` executable are referring to Python 3, so make the appropriate changes to your local machine to ensure compatibility.

# Initial Setup

## Local Dependencies

To run the application locally, you must have the following installed. We recommend using a package manager (like Homebrew on Mac OS X) to install each of the following:

* [Python](https://www.python.org/) (Version 3.10)
* [Docker](https://www.docker.com/) (should include Docker Compose)
* [git](https://git-scm.com/)
* [pre-commit](https://pre-commit.com/)

## Local Setup

1. Clone this repository locally via `git`.
2. Create a new `.env` file from the `.env.example` file by copying the contents of the existing `.env.example` file into your new `.env` file. Add non-placeholder variable values to each variable defined in the `.env` file (where necessary) so that Django can load them correctly.
