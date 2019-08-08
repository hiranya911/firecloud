import argparse
import datetime
import sys

import formatters
import github
import releasenotes


def _extract_release_notes(repo):
    print('Analyzing GitHub history in https://github.com/{0}\n'.format(repo))
    pulls = github.pulls_since_last_release(repo)
    if not pulls:
        print('No new pull requests since the last release.')
        sys.exit(1)

    filtered_pulls = []
    notes = []
    pr_num_len = len(str(pulls[0].number)) + 1
    for pull in pulls:
        pr_info = '{0}: {1}'.format(
            formatters.truncate_or_pad(str(pull.number), pr_num_len),
            formatters.truncate_or_pad(pull.title, 60))
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


def run(repo, version=None, date=None):
    notes = _extract_release_notes(repo)
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

    args = parser.parse_args()

    if not args.repo:
        print('Repo not specified.')
        parser.print_usage()
        sys.exit(1)

    run(args.repo, args.next_version, args.date)
