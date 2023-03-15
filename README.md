
# Opdrachten Team Maintenance

This projects hosts the script we use to perform our bi-weekly maintenance. 

Each project attached must follow our specific setup:
- A make target `upgrade` must exist that updates the requirements to their latest versions.
- A make target `build` must exist that builds the docker images.
- A make target `test` must exist that runs the testcases. 

Once these succeed a new commit is created with the changes and pushed to `feature/maintenance-%y-%m-%d`.

## Installation

First, install `glab` and github CLI `gh`. Then authenticate github CLI

```
gh auth login
glab auth login
```

Clone the repository

```bash
git clone git@git.data.amsterdam.nl:Datapunt/opdrachten-team-maintenance.git
```

Then create a virtual environment. The virtual environment can be empty, dependencies will be installed automatically by the maintenance script.

The script also uses the github and gitlab clis to create PRs, install and setup these tools following the instructions
here:

https://cli.github.com/
https://glab.readthedocs.io/en/latest/

## Usage

Simply run the maintenance script, setting the SLACK_API_TOKEN env var (can be found in vault):

```bash
SLACK_API_TOKEN=xxxx ./maintenance.py
```

