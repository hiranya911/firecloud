import datetime
import itertools
import re
import textwrap

import github
import releasenotes


def wrap_lines(message, max_length=80):
    wrapped = textwrap.wrap(message, max_length, break_long_words=False, break_on_hyphens=False)
    indented = [ '  {0}'.format(line) for line in wrapped[1:] ]
    return '\n'.join([wrapped[0]] + indented)


def group_by_heading(notes):
    grouped_notes = {}
    for key, group in itertools.groupby(notes, lambda p : p.heading):
        if key not in grouped_notes:
            grouped_notes[key] = []
        for commit in group:
            grouped_notes[key].append(commit)
    return grouped_notes


def estimate_next_version(repo, notes):
    version = github.find_last_release(repo)
    major, minor, patch = version.major, version.minor, version.patch
    if any([note.category == releasenotes.Category.CHANGED for note in notes]):
        major += 1
    elif any([note.category == releasenotes.Category.FEATURE for note in notes]):
        minor += 1
    else:
        patch += 1
    return '{0}.{1}.{2}'.format(major, minor, patch)


def estimate_release_date():
    today = datetime.datetime.now()
    tomorrow = today + datetime.timedelta(days=1)
    return tomorrow.strftime('%d %B, %Y')


if __name__ == '__main__':
    repo = 'firebase/firebase-admin-dotnet'
    pulls = github.find_pulls_since_last_release(repo)
    notes = releasenotes.get_release_notes_from_pulls(pulls)
    grouped_notes = group_by_heading(notes)

    next_version = estimate_next_version(repo, notes)
    release_date = estimate_release_date()
    print('Devsite release notes')
    print('## <a name="{0}">Version {0} - {1}</a>'.format(next_version, release_date))
    print()
    for key in sorted(grouped_notes.keys()):
        if key:
            print('### {0}'.format(key))
            print()

        for commit in grouped_notes[key]:
            note = commit.get_devsite_text()
            print('- {0}'.format(wrap_lines(note)))
        print()

    print('\n\nGithub release notes')
    print('## <a name="{0}">Version {0} - {1}</a>'.format(next_version, release_date))
    print()
    for key in sorted(grouped_notes.keys()):
        if key:
            print('### {0}'.format(key))
            print()

        for commit in grouped_notes[key]:
            note = commit.get_github_text()
            print('- {0}'.format(note))
        print()
