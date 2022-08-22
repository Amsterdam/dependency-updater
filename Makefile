test:
	gh auth status
	glab auth status

run: test
	python src/maintenance.py
