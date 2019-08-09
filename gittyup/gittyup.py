import argparse
import datetime
import sys

import formatters
import github
import releasenotes


class CommandLineClient(object):

    def __init__(self, argv=None):
        parser = CommandLineClient._init_parser()
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

    def run(self):
        try:
            self._do_run()
        except Exception as ex:
            print(str(ex))
            sys.exit(1)

    def _do_run(self):
        if not self.repo:
            raise ValueError('Repo not specified.')

        print('Analyzing GitHub history in https://github.com/{0}\n'.format(self.repo))
        pulls = [ p for p in self._find_and_print_pull_requests() if p.has_release_notes ]

        notes = self._extract_release_notes(pulls)
        print('\nExtracted release notes from {0} pull requests.'.format(len(pulls)))

        next_version, estimate = self._get_next_version(notes)
        if estimate:
            print('Estimated next version to be: {0}'.format(next_version))

        if not self.release_date:
            print('Release date not specified. Release date will be set to tomorrow.')

        print()
        self._print_devsite_output(notes, next_version)
        self._print_github_output(notes, next_version)

    def _get_next_version(self, notes):
        if self.next_version:
            return self.next_version, False

        last_version = github.last_release(self.repo)
        version = releasenotes.find_next_version(last_version, notes)
        return version, True

    def _print_devsite_output(self, notes, version):
        print('Devsite release notes')
        print('=====================')
        devsite = formatters.DevsiteFormatter(notes, version, self.release_date)
        print(devsite.printable_output())

    def _print_github_output(self, notes, version):
        print('Github release notes')
        print('====================')
        print(formatters.GitHubFormatter(notes, version).printable_output())

    def _find_and_print_pull_requests(self):
        client = github.Client(self.repo, self.branch)
        pulls = client.pulls_since_last_release()
        if not pulls:
            raise ValueError('No new pull requests since the last release.')

        pr_num_len = len(str(pulls[0].number))
        for pull in pulls:
            pr_info = CommandLineClient._get_pr_summary(pull, pr_num_len)
            if pull.has_release_notes:
                print('{0}  [RELEASE NOTES]'.format(pr_info))
            else:
                print(pr_info)
        return pulls

    def _extract_release_notes(self, pulls):
        notes = []
        for pull in pulls:
            notes.extend(releasenotes.get_release_notes_from_pull(pull))
        return notes

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
        return parser

    @staticmethod
    def _get_pr_summary(pull, pr_num_len):
        pr_desc = '[{0}] {1}'.format(pull.base_branch, pull.title)
        return '{0}: {1}'.format(
            formatters.truncate_or_pad(str(pull.number), pr_num_len),
            formatters.truncate_or_pad(pr_desc, 60))


if __name__ == '__main__':
    client = CommandLineClient()
    client.run()
