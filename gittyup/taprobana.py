from __future__ import print_function

import argparse
import datetime
import os
import sys
import traceback

import formatters
import github
import releasenotes


class Taprobana(object):

    _DEFAULT_SEARCH = github.SearchByPullRequestTitle('Bumped version to')

    def __init__(
        self, repo, branch='master', next_version=None, search_strategy=None,
        verbose=False, stream=sys.stdout, github_token=None):

        self._repo = repo
        self._branch = branch
        self._next_version = next_version
        self._search_strategy = search_strategy if search_strategy else Taprobana._DEFAULT_SEARCH
        self._verbose = verbose
        self._stream = stream
        self._github_token = github_token

    def generate_release_notes(self):
        if not self._repo:
            raise ValueError('Repo not specified.')

        self._v('Analyzing GitHub history in https://github.com/{0}'.format(self._repo))
        if not self._github_token:
            self._v('Accessing GitHub API without authentication credentials')

        client = github.Client(self._repo, self._branch, self._github_token)
        last_release = self._find_last_release_cutoff(client)
        pulls = self._find_pulls_since_last_release(client, last_release)
        notes = self._extract_release_notes(pulls)
        next_version = self._get_next_version(client, notes)
        return notes, next_version

    def print_devsite_output(self, notes, version, release_date=None):
        if not release_date:
            self._v('Release date not specified. Release date will be set to tomorrow.\n')

        self._i('Devsite release notes')
        self._i('=====================')
        devsite = formatters.DevsiteFormatter(notes, version, release_date)
        self._i(devsite.printable_output())

    def print_github_output(self, notes, version):
        self._i('Github release notes')
        self._i('====================')
        self._i(formatters.GitHubFormatter(notes, version).printable_output())

    def _find_last_release_cutoff(self, client):
        self._v('Looking for a {0}'.format(self._search_strategy))
        last_release = self._search_strategy.search(client)
        if last_release:
            desc = last_release.get_description()
            self._v('Found cutoff {0}'.format(formatters.truncate_or_pad(desc, 60)))
        else:
            self._v('No matching cutoff PR was found.')

        self._v()
        return last_release

    def _find_pulls_since_last_release(self, client, last_release):
        pulls = client.find_pulls_since(last_release)
        if not pulls:
            raise ValueError('No new pull requests since the last release.')

        pr_num_len = len(str(max([p.number for p in pulls])))
        for pull in pulls:
            pr_info = Taprobana._get_pr_summary(pull, pr_num_len)
            if pull.has_release_notes:
                self._v('{0}  [RELEASE NOTES]'.format(pr_info))
            else:
                self._v(pr_info)

        self._v()
        return [ p for p in pulls if p.has_release_notes ]

    def _extract_release_notes(self, pulls):
        if not pulls:
            raise ValueError('No pull requests labeled with release notes.')

        notes = []
        for pull in pulls:
            notes.extend(releasenotes.get_release_notes_from_pull(pull))
        self._v('Extracted release notes from {0} pull requests.'.format(len(pulls)))
        return notes

    def _get_next_version(self, client, notes):
        if self._next_version:
            return self._next_version

        last_version = client.find_last_release_version()
        next_version = releasenotes.find_next_version(last_version, notes)
        version_string = '{0}.{1}.{2}'.format(*next_version)
        self._v('Estimated next version to be: {0}'.format(version_string))
        return version_string

    def _v(self, msg=''):
        if self._verbose:
            print(msg, file=self._stream)

    def _i(self, msg=''):
        print(msg, file=self._stream)

    @staticmethod
    def _get_pr_summary(pull, pr_num_len):
        pr_desc = u'[{0}] {1}'.format(pull.base_branch, pull.title)
        return '{0}: {1}'.format(
            formatters.truncate_or_pad(str(pull.number), pr_num_len),
            formatters.truncate_or_pad(pr_desc, 60))


class CommandLineConfig(object):

    def __init__(self, argv=None):
        parser = CommandLineConfig._init_parser()
        self._args = parser.parse_args(argv)

    @property
    def repo(self):
        return self._args.repo

    @property
    def branch(self):
        if self._args.branch == '*':
            return None
        return self._args.branch

    @property
    def next_version(self):
        return self._args.next_version

    @property
    def release_date(self):
        date = self._args.date
        if date:
            return datetime.datetime.strptime(date, '%Y-%m-%d')
        return None

    @property
    def search_strategy(self):
        if self._args.since_pr:
            return github.SearchByPullRequestNumber(self._args.since_pr)
        elif self._args.commit_sha:
            return github.SearchByCommitSha(self._args.commit_sha)
        elif self._args.commit_prefix:
            return github.SearchByCommitMessage(self._args.commit_prefix)
        elif self._args.title_prefix:
            return github.SearchByPullRequestTitle(self._args.title_prefix)
        return None

    @property
    def verbose(self):
        return not self._args.quiet

    @property
    def github_token(self):
        if self._args.token:
            return self._args.token
        return os.environ.get('TAPROBANA_GITHUB_TOKEN')

    @staticmethod
    def _init_parser():
        parser = argparse.ArgumentParser(description='Generate release notes for GitHub repo.')
        parser.add_argument(
            'repo',
            metavar='REPO',
            help='Name of the Github repo in "organization/repo-name" format.')
        parser.add_argument(
            '--next-version',
            help='The next semver version to be included in release notes.')
        parser.add_argument(
            '--date',
            help='Release date to be included in release notes in yyyy-mm-dd format.')
        parser.add_argument(
            '--branch',
            default='master',
            help=('Name of the branch to scan for pull requests. Defaults to master. Use * to'
                  ' consider all branches.'))
        parser.add_argument(
            '--since-pr',
            type=int,
            help=('Pull request number that will be used as the cutoff for the last release.'
                  ' If not specified looks for a pull request for title prefix match.'))
        parser.add_argument(
            '--title-prefix',
            help=('Title prefix string to match when searching for the last release pull request.'
                  ' Defaults to the prefix "Bumped version to".'))
        parser.add_argument(
            '--commit-prefix',
            help='Commit prefix string to match when searching for the last release commit.')
        parser.add_argument(
            '--commit-sha',
            help='Commit sha string to use when searching for the last release commit.')
        parser.add_argument(
            '--token',
            help=('GitHub access token to authorize API calls with. Can also be specified by'
                  ' setting the TAPROBANA_GITHUB_TOKEN environment variable.'))
        parser.add_argument(
            '--quiet',
            action='store_true',
            default=False,
            help='Run in the quiet mode. Print only the release notes without verbose info.')
        return parser


if __name__ == '__main__':
    config = CommandLineConfig()
    taprobana = Taprobana(
        config.repo, branch=config.branch, next_version=config.next_version,
        search_strategy=config.search_strategy, verbose=config.verbose,
        github_token=config.github_token)

    try:
        notes, next_version = taprobana.generate_release_notes()
        taprobana.print_devsite_output(notes, next_version, config.release_date)
        taprobana.print_github_output(notes, next_version)
    except Exception as ex:
        print(traceback.format_exc())
        sys.exit(1)
