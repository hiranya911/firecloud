import argparse
import datetime
import sys

import formatters
import github
import releasenotes


def _get_pr_summary(pull, pr_num_len):
    pr_desc = '[{0}] {1}'.format(pull.base_branch, pull.title)
    return '{0}: {1}'.format(
        formatters.truncate_or_pad(str(pull.number), pr_num_len),
        formatters.truncate_or_pad(pr_desc, 60))


def _extract_release_notes(repo, branch=None):
    print('Analyzing GitHub history in https://github.com/{0}\n'.format(repo))
    client = github.Client(repo, branch)
    pulls = client.pulls_since_last_release()
    if not pulls:
        print('No new pull requests since the last release.')
        sys.exit(1)

    filtered_pulls = []
    notes = []
    pr_num_len = len(str(pulls[0].number))
    for pull in pulls:
        pr_info = _get_pr_summary(pull, pr_num_len)
        if pull.has_release_notes:
            print('{0}  [RELEASE NOTES]'.format(pr_info))
            filtered_pulls.append(pull)
            notes.extend(releasenotes.get_release_notes_from_pull(pull))
        else:
            print(pr_info)

    if not filtered_pulls:
        print('Could not find any pull requests labeled with release-notes.')
        sys.exit(1)

    print('\nExtracted release notes from {0} pull requests.'.format(len(filtered_pulls)))
    return notes


def run(repo, branch=None, version=None, date=None):
    notes = _extract_release_notes(repo, branch)
    if not version:
        last_version = github.last_release(repo)
        version = releasenotes.find_next_version(last_version, notes)
        print('Estimated next version to be: {0}'.format(version))

    release_date = None
    if date:
        release_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        print('Release date not specified. Release date will be set to tomorrow.')

    print()
    print('Devsite release notes')
    print('=====================')
    print(formatters.DevsiteFormatter(notes, version, release_date).printable_output())

    print('Github release notes')
    print('====================')
    print(formatters.GitHubFormatter(notes, version).printable_output())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate release notes for GitHub repo.')
    parser.add_argument(
        'repo', metavar='REPO', help='Name of the Github repo in "organization/repo-name" format.')
    parser.add_argument(
        '--next-version', help='The next semver version to be included in release notes.')
    parser.add_argument(
        '--date', help='Release date to be included in release notes in yyyy-mm-dd format.')
    parser.add_argument(
        '--branch',
        default='master',
        help=('Name of the branch to scan for pull requests. Defaults to master. Use * to'
              ' consider all branches.'))

    args = parser.parse_args()

    if not args.repo:
        print('Repo not specified.')
        parser.print_usage()
        sys.exit(1)

    branch = args.branch
    if branch == '*':
        branch = None

    run(args.repo, branch, args.next_version, args.date)
