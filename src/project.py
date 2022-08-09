# standard library
import re
import shlex
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from functools import partial, cached_property
from pathlib import Path
from subprocess import Popen, PIPE, CalledProcessError, check_output, STDOUT
from sys import stdout, stderr
from threading import Lock, Thread
from typing import List
# 1st party
from slack import slack


WORKDIR = Path(__file__).parent / 'workdir'


@dataclass
class Project:

    name: str
    git_uri: str
    timetell: int
    acceptance_pipeline: str
    production_pipeline: str
    acceptance_urls: List[str]
    production_urls: List[str]
    auth: str
    pr_url: str = field(default='No pr', init=False)

    @property
    def url(self):
        # add https scheme and strip .git
        return self.git_uri.replace(':', '/').replace('git@', 'https://')[:-4]

    @cached_property
    def latest_tag(self):
        command = [
            "git",
            "for-each-ref",
            "--sort=-creatordate",
            "--format",
            "%(refname)",
            "refs/tags",
        ]
        lines = check_output(command, cwd=self.cwd).decode().splitlines()
        tags = [
            tag.split('/')[-1].strip("'")
            for tag in lines
            if re.match(r"^refs/tags/v?\d+\.\d+\.\d+$", tag)  # only find semver tags
        ]
        return tags[0]

    @property
    def next_tag(self):
        tokens = self.latest_tag.split('.')
        tokens[-1] = str(int(tokens[-1]) + 1)
        return '.'.join(tokens)

    @property
    def tag_url(self):
        url = self.url
        if 'github' in url:
            title = urllib.parse.quote_plus(f'Maintenance run {date.today()}')
            return f'{url}/releases/new?tag={self.next_tag};title={title}'
        elif 'git.data.amsterdam' in url:
            return f'{url}/-/tags/new?tag_name={self.next_tag}'
        else:
            return url

    @property
    def acceptance_urls_str(self):
        return '\n'.join(self.acceptance_urls)

    @property
    def production_urls_str(self):
        return '\n'.join(self.production_urls)
    
    @property
    def cwd(self):
        return WORKDIR / self.name

    def git(self, *args):
        self.subprocess('git', *args)

    def make(self, *args):
        self.subprocess('make', *args)

    def subprocess(self, *args):
        print(f'{self.name}> {shlex.join(args)}')
        process = Popen(args, stdout=PIPE, stderr=STDOUT, cwd=self.cwd)

        for line in process.stdout:
            print(f'{self.name}> {line}')

        process.communicate()
        if process.returncode:
            raise CalledProcessError(process.returncode, args)

    def create_pr(self):
        if 'github' in self.url:
            output = check_output(['gh', 'pr', 'create', '--fill'], cwd=self.cwd)
            self.pr_url = output.decode().splitlines()[-1]
        elif 'git.data.amsterdam.nl' in self.url:
           output = check_output(['glab', 'mr', 'create', '--fill', '--yes'], cwd=self.cwd)
           self.pr_url = output.decode().splitlines()[0]
        else:
            print(f"Ik weet niet hoe ik een PR moet maken voor {self.url}")

    def send_to_slack(self):
        message_id = slack(self.name)

        slack_thread = partial(slack, thread=message_id)
        slack_thread('1. Review Pull Request', self.pr_url, ':eyes:')
        slack_thread('2. Release Naar Acceptatie (merge naar master)', self.pr_url, ':twisted_rightwards_arrows:')
        slack_thread('3. Controleer Acceptatie Deployment Job', self.acceptance_pipeline, ':jenkins_ci:')
        slack_thread('4. Controleer Acceptatie', self.acceptance_urls_str, ':rocket:')
        slack_thread('5. Release Naar Productie (tag versie)', self.tag_url, ':label:')
        slack_thread(
            '6. Controleer Productie Deployment Job',
            f'{self.production_pipeline}job/{self.next_tag}/',
            ':jenkins_ci:',
        )
        slack_thread('7. Controleer Productie', self.production_urls_str, ':rocket:')
