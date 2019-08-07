import sys
import textwrap

import github
import releasenotes


def _print_wrapped(line, max_length=80):
    if len(line) <= max_length:
        print(line)
        return
    wrapped = textwrap.wrap(line, max_length, break_long_words=False, break_on_hyphens=False)
    indented = [ '  {0}'.format(part) for part in wrapped[1:] ]
    print('\n'.join([wrapped[0]] + indented))


def print_devsite_release_notes(next_version, text, max_length=80):
    print('Devsite release notes:')
    release_date = releasenotes.estimate_release_date()
    print('## <a name="{0}">Version {0} - {1}</a>\n'.format(next_version, release_date))

    lines = text.splitlines()
    for line in lines:
        _print_wrapped(line)


def print_github_release_notes(next_version, text):
    print('Github release notes:')
    print('v{0}\n'.format(next_version))
    print(releasenotes.get_github_text(text))


if __name__ == '__main__':
    repo = 'firebase/firebase-admin-dotnet'
    pulls = github.find_pulls_since_last_release(repo)
    if not pulls:
        print('Could not find any pull requests labeled with release-notes')
        sys.exit(1)

    print('Extracting release notes from {0} pull requests...'.format(len(pulls)))
    for pull in pulls:
        print('{0}: {1}'.format(pull.number, pull.title))
    print()

    notes = releasenotes.get_release_notes_from_pulls(pulls)

    last_version = github.find_last_release(repo)
    next_version = releasenotes.estimate_next_version(last_version, notes)
    text = releasenotes.generate_for_devsite(notes)

    print_devsite_release_notes(next_version, text)
    print()
    print_github_release_notes(next_version, text)
