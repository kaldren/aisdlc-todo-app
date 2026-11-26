.PHONY: setup test run prod smoke release-check status lines

setup:
	uv sync
	git config core.hooksPath .githooks
	chmod +x bin/sdlc scripts/*.sh .githooks/*

test:
	uv run pytest -q

run:
	uv run uvicorn app.main:app --reload --port 8000

prod:
	mkdir -p var/log
	uv run uvicorn app.main:app --port 8000 --no-access-log

smoke:
	scripts/smoke.sh

release-check: test smoke

status:
	bin/sdlc status

lines:
	bin/sdlc lines
