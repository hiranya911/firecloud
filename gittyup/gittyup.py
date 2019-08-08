import argparse
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

    print('\nExtracted release notes from {0} pull requests.\n'.format(len(filtered_pulls)))
    return notes


def run(repo):
    notes = _extract_release_notes(repo)
    last_version = github.last_release(repo)

    print('Devsite release notes')
    print('=====================')
    print(formatters.DevsiteFormatter(notes, last_version).printable_output())

    print('Github release notes')
    print('====================')
    print(formatters.GitHubFormatter(notes, last_version).printable_output())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate release notes for GitHub repo.')
    parser.add_argument('repo')
    args = parser.parse_args()

    if not args.repo:
        print('Repo not specified.')
        parser.print_usage()
        sys.exit(1)

    run(args.repo)
