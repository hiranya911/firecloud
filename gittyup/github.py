import requests

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


def _has_title_prefix(pull):
    return pull.title.startswith('Bumped version to')


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


def _find_all_pulls_since_last_release(repo, is_last_release):
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


def find_pulls_since_last_release(repo, is_last_release=_has_title_prefix):
    all_pulls = _find_all_pulls_since_last_release(repo, is_last_release)
    return [ pull for pull in all_pulls if pull.is_release_note ]


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
