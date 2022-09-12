test:
	gh auth status
	glab auth status -h git.data.amsterdam.nl

run: test
	python src/maintenance.py
