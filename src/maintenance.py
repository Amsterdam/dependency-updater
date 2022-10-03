#!/usr/bin/env python3

# standard library
import json
import sys
import os
import shutil
from datetime import date
from subprocess import check_output

# 1st party
from diff import git_diff, parse_diff, post_package_updates_to_slack
from project import Project
from settings import PROJECTS_JSON, WORKDIR

PROJECTS = [Project(**project) for project in json.loads(PROJECTS_JSON.read_text())]

DATE = date.today().strftime("%Y-%m-%d")
BRANCH = f"feature/maintenance-{DATE}"

package_changes = []

shutil.rmtree(WORKDIR, ignore_errors=True)
os.makedirs(WORKDIR)

failed_projects = {}

try:
    only_run = sys.argv[1]
except IndexError:
    only_run = None

if only_run:
    PROJECTS = list(filter(lambda x: x.name == only_run, PROJECTS))
    if len(PROJECTS) == 0:
        print('No project found')

# Upgrade dependencies
for project in PROJECTS:
    if not project.enabled:
        print(f'\33[32m project {project.name} is disabled \033[33m')
        continue
    check_output(['git', 'clone', project.git_uri], cwd=WORKDIR)
    project.git('checkout', 'master')
    project.git('checkout', '-B', BRANCH)
    project.make('clean')
    project.make('requirements')
    diff = git_diff(project.cwd)
    package_changes.append((project, parse_diff(diff)))
    try:
        project.make('build')
        project.make('test')
        project.successful = True
    except Exception as e:
        failed_projects[project.name] = e
        project.successful = False
    project.make('clean')
    project.git('add', 'requirements.txt', 'requirements_dev.txt')
    project.git('commit', '-m', f'Maintenance run {DATE}')
    project.git('push', '-u', 'origin', '--force', BRANCH)

# Post package upgrades to slack
# post_package_updates_to_slack(package_changes)

# Create prs
for project in PROJECTS:
    if not project.enabled:
        continue
    project.create_pr()
    # project.send_to_slack()
