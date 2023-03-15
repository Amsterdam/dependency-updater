#!/usr/bin/env python3

import copy
import os
import shutil
from datetime import date
from pathlib import Path
from subprocess import check_output

from diff import git_diff, parse_diff, post_package_updates_to_slack
from project import Project


class DependencyUpdater:
    def __init__(self, projects_json: dict, workdir: Path):
        self.projects = [Project(workdir=workdir, **project) for project in projects_json]

        self.date = date.today().strftime("%Y-%m-%d")
        self.branch = f"feature/maintenance-{self.date}"
        self.package_changes = []
        self.failed_projects = {}
        self.workdir = workdir

        shutil.rmtree(workdir, ignore_errors=True)
        os.makedirs(workdir, exist_ok=True)

    def run(self, project_name: str = None):
        projects = copy.copy(self.projects)
        if project_name:
            # Select and run only the project with the given name
            projects = list(filter(lambda x: x.name == project_name, self.projects))
            if len(projects) == 0:
                print(f'No project found with name {project_name}')

        for project in projects:
            print(f"Running for project {project}")
            self._update_project_requirements(project)

        # Post package upgrades to slack
        post_package_updates_to_slack(self.package_changes)

        # Create prs
        for project in projects:
            if not project.enabled:
                continue
            project.create_pr()
            project.send_to_slack()

    def _update_project_requirements(self, project: Project):
        if not project.enabled:
            print(f'\33[32m project {project.name} is disabled \033[33m')
            return

        check_output(['git', 'clone', project.git_uri], cwd=self.workdir)
        project.git('checkout', 'master')
        project.git('checkout', '-B', self.branch)
        project.make('clean')
        project.make('requirements')
        diff = git_diff(project.cwd)
        self.package_changes.append((project, parse_diff(diff)))
        try:
            project.make('build')
            project.make('test')
            project.successful = True
        except Exception as e:
            self.failed_projects[project.name] = e
            project.successful = False
        project.make('clean')
        project.git('add', 'requirements.txt', 'requirements_dev.txt')
        project.git('commit', '-m', f'Maintenance run {self.date}')
        project.git('push', '-u', 'origin', '--force', self.branch)


