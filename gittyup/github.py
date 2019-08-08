import requests
import json


class User(object):

    def __init__(self, data):
        self._data = data

    @property
    def login(self):
        return self._data['login']

    @property
    def url(self):
        return self._data['html_url']


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
    def has_release_notes(self):
        return 'release-note' in self.labels

    @property
    def is_contribution(self):
        return self._data['author_association'] == 'CONTRIBUTOR'

    @property
    def user(self):
        return User(self._data['user'])

    @property
    def url(self):
        return self._data['html_url']


def _has_title_prefix(pull):
    return pull.number == 82


def _get_page(repo, page_number=1, base_branch='master'):
    url = 'https://api.github.com/repos/{0}/pulls'.format(repo)
    params = {
      'state': 'closed',
      'base': base_branch,
      'page': page_number,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def find_pulls_since_last_release(repo, is_last_release=_has_title_prefix):
    pulls = []
    proceed = True
    page_number = 1
    while proceed:
        page = [PullRequest(pull) for pull in _get_page(repo, page_number)]
        if not page:
            proceed = False
            continue

        filtered = []
        for pull in page:
            if is_last_release(pull):
                proceed = False
                break
            filtered.append(pull)
        pulls.extend(filtered)
        page_number += 1

    return pulls


class SemVer(object):

    def __init__(self, tag_name):
        if tag_name.startswith('v'):
            tag_name = tag_name[1:]
        self._segments = tag_name.split('.')

    @property
    def major(self):
        return int(self._segments[0])

    @property
    def minor(self):
        return int(self._segments[1])

    @property
    def patch(self):
        return int(self._segments[2])


def find_last_release(repo):
    url = 'https://api.github.com/repos/{0}/releases'.format(repo)
    response = requests.get(url)
    response.raise_for_status()
    tag_name = response.json()[0]['tag_name']
    return SemVer(tag_name)
