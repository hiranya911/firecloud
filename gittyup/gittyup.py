import itertools
import re
import textwrap

import requests


SCOPES = {
  'fcm': 'Firebase Cloud Messaging',
}


class PullRequest(object):

    def __init__(self, data):
        self._data = data

    @property
    def title(self):
        return self._data['title']

    @property
    def body(self):
        return self._data['body']

    @property
    def number(self):
        return self._data['number']

    @property
    def labels(self):
        return [label['name'] for label in self._data['labels']]

    @property
    def is_release_note(self):
        return 'release-note' in self.labels


class ConventionalCommit(object):

    PATTERN = re.compile(r'(?P<type>\w+)(\((?P<scope>\w+)\))?:\s+(?P<desc>.+)')

    def __init__(self, pr_type, description, scope='', body=''):
        self.type = pr_type
        self._description = description
        self._scope = scope
        self.body = body

    @property
    def scope(self):
        return SCOPES.get(self._scope, self._scope)

    @property
    def descriptions(self):
        lines = self.body.splitlines()
        descs = []
        for line in lines:
            if line.startswith('RELEASE NOTE:'):
                descs.append(line[14:])

        return descs if descs else [ self._description ]

    @property
    def _category(self):
        if 'API CHANGE:' in self.body:
            return '{{changed}}'
        elif self.type == 'feat':
            return '{{feature}}'
        else:
            return '{{fixed}}'

    def get_release_notes(self):
        return [
          '{0} {1}'.format(self._category, with_full_stop(desc))
          for desc in self.descriptions
        ]


    @staticmethod
    def parse_pull_request(pull):
        title_match = ConventionalCommit.PATTERN.search(pull.title)
        if title_match:
            return ConventionalCommit(
                title_match.group('type'),
                title_match.group('desc'),
                title_match.group('scope'),
                pull.body)

        return ConventionalCommit('fix', pull.title, body=pull.body)


def get_page(repo, page_number=1, base_branch='master'):
    url = 'https://api.github.com/repos/{0}/pulls'.format(repo)
    params = {
      'state': 'closed',
      'base': base_branch,
      'page': page_number,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def find_pulls_since_last_release(repo):
    page_number = 1
    pulls = []
    proceed = True
    while proceed:
        page = [PullRequest(pull) for pull in get_page(repo, page_number)]
        if not page:
            proceed = False
            continue

        filtered = []
        for pull in page:
            if pull.title.startswith('Bumped version to'):
                proceed = False
                break
            filtered.append(pull)
        pulls.extend(filtered)
        page_number += 1

    return pulls


def with_full_stop(message):
    return message if message.endswith('.') else '{0}.'.format(message)


def wrap_lines(message, max_length=80):
    wrapped = textwrap.wrap(message, max_length, break_long_words=False, break_on_hyphens=False)
    indented = [ '  {0}'.format(line) for line in wrapped[1:] ]
    return '\n'.join([wrapped[0]] + indented)


if __name__ == '__main__':
    repo = 'firebase/firebase-admin-dotnet'
    pulls = [ pull for pull in find_pulls_since_last_release(repo) if pull.is_release_note ]
    parsed_commits = [ ConventionalCommit.parse_pull_request(pull) for pull in pulls ]
    grouped_commits = {}
    for key, group in itertools.groupby(parsed_commits, lambda p : p.scope):
        if key not in grouped_commits:
            grouped_commits[key] = []
        for commit in group:
            grouped_commits[key].append(commit)

    print('## <a name="1.8.0">Version 1.8.0 - August 07, 2019</a>')
    print()
    for key in sorted(grouped_commits.keys()):
        if key:
            print('### {0}'.format(key))
            print()

        for commit in grouped_commits[key]:
            for note in commit.get_release_notes():
              print('- {0}'.format(wrap_lines(note)))
        print()
