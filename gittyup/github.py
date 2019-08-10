import datetime

import requests


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

    _GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

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

    @property
    def base_branch(self):
        return self._data['base']['ref']

    @property
    def updated_at(self):
        return datetime.datetime.strptime(
            self._data['updated_at'], PullRequest._GITHUB_DATE_FORMAT)

    @property
    def closed_at(self):
        return datetime.datetime.strptime(
            self._data['closed_at'], PullRequest._GITHUB_DATE_FORMAT)


class PullRequestSearchStrategy(object):

    def search(self, repo, branch=None):
        raise NotImplementedError


class SearchByTitlePrefix(PullRequestSearchStrategy):

    def __init__(self, prefix):
        self._prefix = prefix

    def search(self, repo, branch=None):
        query = [
            'repo:{0}'.format(repo),
            'is:pr',
            'state:closed',
            '{0}:in:title'.format(self._prefix),
        ]
        if branch:
            query.append('base:{0}'.format(branch))

        url = 'https://api.github.com/search/issues?q={0}'.format('+'.join(query))
        params = {
            'sort': 'updated',
            'direction': 'desc',
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        body = response.json()
        if body.get('total_count', 0) > 0:
            items = body.get('items')
            return PullRequest(items[0])
        return None

    def __str__(self):
        return 'TitlePrefix = "{0}"'.format(self._prefix)


class SearchByNumber(PullRequestSearchStrategy):

    def __init__(self, number):
        self._number = number

    def search(self, repo, branch=None):
        url = 'https://api.github.com/repos/{0}/pulls/{1}'.format(repo, self._number)
        response = requests.get(url)
        response.raise_for_status()
        return PullRequest(response.json())

    def __str__(self):
        return 'Number = {0}'.format(self._number)


class Client(object):

    def __init__(self, repo, base_branch=None):
        self._repo = repo
        self._base_branch = base_branch

    def find_pulls_since(self, cutoff_pull=None):
        cutoff = cutoff_pull.closed_at if cutoff_pull else None

        pulls = []
        proceed = True
        page_number = 1
        while proceed:
            page = self._get_page(page_number)
            if not page:
                proceed = False
                continue

            filtered = []
            for pull in page:
                # updated_at >= closed_at: When we see the first PR whose updated_at is before
                # the cutoff, we can be sure that PR and all the ones after it were closed before
                # the cutoff.
                if cutoff and pull.updated_at < cutoff:
                    proceed = False
                    break
                filtered.append(pull)
            pulls.extend(filtered)
            page_number += 1

        if cutoff:
            pulls = [pull for pull in pulls if pull.closed_at > cutoff]

        return pulls

    def find_last_release_version(self):
        url = 'https://api.github.com/repos/{0}/releases'.format(self._repo)
        response = requests.get(url)
        response.raise_for_status()
        tag_name = response.json()[0]['tag_name']
        if tag_name.startswith('v'):
            tag_name = tag_name[1:]
        return tuple([ int(x) for x in tag_name.split('.') ])

    def _get_page(self, page_number=1):
        url = 'https://api.github.com/repos/{0}/pulls'.format(self._repo)
        params = {
            'state': 'closed',
            'page': page_number,
            'sort': 'updated',
            'direction': 'desc',
        }
        if self._base_branch:
            params['base'] = self._base_branch
        response = requests.get(url, params=params)
        response.raise_for_status()
        return [ PullRequest(p) for p in response.json() ]
