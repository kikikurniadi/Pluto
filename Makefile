.PHONY: venv deps test frontend-build run lint

venv:
	python3 -m venv agents/venv
	agents/venv/bin/pip install --upgrade pip

deps: venv
	agents/venv/bin/pip install -r agents/requirements.txt

test:
	PYTHONPATH=agents agents/venv/bin/pytest -q

frontend-build:
	cd frontend && npm ci && npm run build

run:
	bash run_all.sh

lint:
	# add linting steps if needed
	echo "no linter configured"
