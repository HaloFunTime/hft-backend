DJANGO_RUNNING := $(shell docker inspect -f '{{.State.Running}}' django)
POSTGRES_RUNNING := $(shell docker inspect -f '{{.State.Running}}' postgres)

main:
	pre-commit install
	docker-compose up --build

kill:
	docker-compose down

djangoruncheck:
ifneq ($(DJANGO_RUNNING), true)
	$(error Django is not running, start it with 'make')
endif

postgresruncheck:
ifneq ($(POSTGRES_RUNNING), true)
	$(error PostgreSQL is not running, start it with 'make')
endif

createsuperuser: djangoruncheck
	docker exec -it django python manage.py createsuperuser

migrations: djangoruncheck
	docker exec -it django python manage.py makemigrations

migrate: djangoruncheck
	docker exec -it django python manage.py migrate

startapp: djangoruncheck
ifdef appname
	docker exec -it django python manage.py startapp $(appname)
else
	$(error 'make startapp' requires an 'appname')
endif

startsubapp: djangoruncheck
ifneq ($(and $(appname),$(subappname)),)
	docker exec -it django sh -c 'cd $(appname) && python ../manage.py startapp $(subappname)'
else
	$(error 'make startsubapp' requires an 'appname' and 'subappname')
endif
