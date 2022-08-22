# standard library
import json
import pkg_resources
import urllib.request
from collections import namedtuple
from contextlib import suppress
from distutils.version import StrictVersion
from functools import partial
from itertools import groupby
from subprocess import check_output
from typing import Iterable, NamedTuple, List, Tuple
# 1st party
from project import Project
from slack import slack


def git_diff(cwd) -> Iterable[str]:
    """
    Run git diff in the specified directory.
    """
    return check_output(['git', 'diff', 'requirements.txt'], cwd=cwd).decode().splitlines()


class PackageChange(NamedTuple):
    package: str
    from_version: str
    to_version: str


def normalise_package_name(package_name):
    """
    Ensure we always use the same package names when parsing git diff
    sometimes a package is referred to using - and sometimes with . (I
    think depending on pip version).
    """
    data = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json"))
    return data['info']['name']


def parse_diff(diff: Iterable[str]) -> List[PackageChange]:
    """
    Parse a git diff to find changes to dependencies.

    :param diff: The output from git diff

    :return: Iterable of package changes.
    """
    def get_change_type(line):
        for char in '-+':
            # filter single line changes
            if line.startswith(char) and not line.startswith(char * 3):
                return char

    # because we are parsing from a pip-tools generated file the specifier
    # should always be of the form ==version, so we strip the first two
    # characters
    # TODO: assert this assumption
    LineChange = namedtuple('LineChange', 'change_type package version')
    changes = {
        LineChange(change_type, normalise_package_name(requirement.key), str(requirement.specifier)[2:])
        for line in diff
        if (change_type := get_change_type(line)) is not None
        if (requirement := next(pkg_resources.parse_requirements(line[1:]), None)) is not None
    }

    def version(package, change_type):
        changes_for_this_package_of_type = (
            c.version
            for c in changes
            if c.package == package
            if c.change_type == change_type
        )
        return next(changes_for_this_package_of_type, None)

    return [
        PackageChange(package, from_version, to_version)
        for package in {c.package for c in changes}
        if (from_version := version(package, '-')) != (to_version := version(package, '+'))
    ]


def post_package_updates_to_slack(project_package_changes: Iterable[Tuple[Project, List]]):
    """
    Create threads on slack which show the major dependency upgrades
    and the projects that are affected.
    """
    all_package_updates = sorted([
        (package_change, project.name)
        for project, package_changes in project_package_changes
        for package_change in package_changes
    ])

    messages = []

    for package_change, group in groupby(all_package_updates, key=lambda x: x[0]):

        show_message = True

        if package_change.to_version is not None and package_change.from_version is not None:
            # if one of the versions is not strict, so we can't say anything about if this is a patch
            # release or not so we just show the message to be sure
            with suppress(ValueError):
                strict_from_version = StrictVersion(package_change.from_version)
                strict_to_version = StrictVersion(package_change.to_version)
                show_message = strict_from_version.version[0] != strict_to_version.version[0]

            if package_change.from_version < package_change.to_version:
                icon_emoji = ':arrow_up:'
                message = f'{package_change.from_version} ➪ {package_change.to_version}'
            else:
                icon_emoji = ':arrow_down:'
                message = f'{package_change.from_version} ➪ {package_change.to_version}'

            if show_message:
                messages.append((package_change.package, icon_emoji, message, list(group)))

    if messages:
        slack('---------------------------------')
        for package, icon_emoji, message, group in sorted(messages):
            message_id = slack(header=f'{package} | {message}', icon_emoji=icon_emoji)
            slack_thread = partial(slack, thread=message_id)
            slack_thread(text='\n'.join(project for package_update, project in group))
            slack_thread(text=f'https://pypi.org/project/{package}/#history')
        slack('---------------------------------')
    else:
        slack('---------------------------------')
        slack('No major upgrades to dependencies')
        slack('---------------------------------')

