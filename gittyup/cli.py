import argparse
import datetime
import sys

import formatters
import github
import releasenotes


class Application(object):

    def __init__(self, argv=None):
        parser = Application._init_parser()
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
            return github.SearchByNumber(self._args.since_pr)
        else:
            return github.SearchByTitlePrefix(self._args.title_prefix)

    def run(self):
        try:
            self._do_run()
        except Exception as ex:
            print(str(ex))
            sys.exit(1)

    def _do_run(self):
        if not self.repo:
            raise ValueError('Repo not specified.')

        print('Analyzing GitHub history in https://github.com/{0}'.format(self.repo))
        client = github.Client(self.repo, self.branch)

        last_release = self._find_last_release_pull()
        pulls = self._find_pulls_since_last_release(client, last_release)
        notes = self._extract_release_notes(pulls)
        next_version = self._get_next_version(client, notes)

        self._print_devsite_output(notes, next_version)
        self._print_github_output(notes, next_version)

    def _find_last_release_pull(self):
        print('Looking for a pull request with: {{ {0} }}'.format(self.search_strategy))
        last_release = self.search_strategy.search(self.repo, self.branch)
        if last_release:
            print('Found cutoff PR: [{0}] {1}'.format(
                last_release.number, formatters.truncate_or_pad(last_release.title, 60)))
        else:
            print('No matching cutoff PR was found.')

        print('')
        return last_release

    def _find_pulls_since_last_release(self, client, last_release):
        pulls = client.find_pulls_since(last_release)
        if not pulls:
            raise ValueError('No new pull requests since the last release.')

        pr_num_len = len(str(pulls[0].number))
        for pull in pulls:
            pr_info = Application._get_pr_summary(pull, pr_num_len)
            if pull.has_release_notes:
                print('{0}  [RELEASE NOTES]'.format(pr_info))
            else:
                print(pr_info)

        print('')
        return [ p for p in pulls if p.has_release_notes ]

    def _extract_release_notes(self, pulls):
        if not pulls:
            raise ValueError('No pull requests labeled with release notes.')

        notes = []
        for pull in pulls:
            notes.extend(releasenotes.get_release_notes_from_pull(pull))
        print('Extracted release notes from {0} pull requests.'.format(len(pulls)))
        return notes

    def _get_next_version(self, client, notes):
        if self.next_version:
            return self.next_version

        last_version = client.find_last_release_version()
        next_version = releasenotes.find_next_version(last_version, notes)
        version_string = '{0}.{1}.{2}'.format(*next_version)
        print('Estimated next version to be: {0}'.format(version_string))
        return version_string

    def _print_devsite_output(self, notes, version):
        if not self.release_date:
            print('Release date not specified. Release date will be set to tomorrow.\n')

        print('Devsite release notes')
        print('=====================')
        devsite = formatters.DevsiteFormatter(notes, version, self.release_date)
        print(devsite.printable_output())

    def _print_github_output(self, notes, version):
        print('Github release notes')
        print('====================')
        print(formatters.GitHubFormatter(notes, version).printable_output())

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
            default='Bumped version to',
            help=('Title prefix string to match when searching for the last release pull request.'
                  ' Defaults to the prefix "Bumped version to".'))
        return parser

    @staticmethod
    def _get_pr_summary(pull, pr_num_len):
        pr_desc = '[{0}] {1}'.format(pull.base_branch, pull.title)
        return '{0}: {1}'.format(
            formatters.truncate_or_pad(str(pull.number), pr_num_len),
            formatters.truncate_or_pad(pr_desc, 60))