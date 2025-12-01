SHELL := /bin/bash

.PHONY: start stop restart status

start:
	./scripts/manage.sh start

stop:
	./scripts/manage.sh stop

restart:
	./scripts/manage.sh restart

status:
	./scripts/manage.sh status
