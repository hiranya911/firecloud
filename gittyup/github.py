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


class SemVer(object):

    def __init__(self, tag_name):
        if tag_name.startswith('v'):
            tag_name = tag_name[1:]
        self.segments = [ int(x) for x in tag_name.split('.') ]

    @property
    def major(self):
        return self.segments[0]

    @property
    def minor(self):
        return self.segments[1]

    @property
    def patch(self):
        return self.segments[2]


def last_release(repo):
    url = 'https://api.github.com/repos/{0}/releases'.format(repo)
    response = requests.get(url)
    response.raise_for_status()
    tag_name = response.json()[0]['tag_name']
    return SemVer(tag_name)


class SearchStrategy(object):

    def __init__(self, repo):
        self.repo = repo

    def find(self):
        raise NotImplementedError


class TitlePrefixSearch(SearchStrategy):

    _DEFAULT_PREFIX = '"Bumped version to"'

    def __init__(self, repo, prefix=_DEFAULT_PREFIX, branch=None):
        super().__init__(repo)
        self.prefix = prefix
        self.branch = branch

    def find(self):
        query = [
            'repo:{0}'.format(self.repo),
            'is:pr',
            'state:closed',
            '{0}:in:title'.format(self.prefix),
        ]
        if self.branch:
            query.append('base:{0}'.format(self.branch))

        url = 'https://api.github.com/search/issues?q={0}'.format('+'.join(query))
        params = {
            'sort': 'updated',
            'direction': 'desc',
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        body = response.json()
        print(response.request.url)
        if body.get('total_count', 0) > 0:
            items = body.get('items')
            return PullRequest(items[0])
        return None


class PullRequestSearch(SearchStrategy):

    def __init__(self, repo, number):
        super().__init__(repo)
        self.number = number

    def find(self):
        url = 'https://api.github.com/repos/{0}/pulls/{1}'.format(self.repo, self.number)
        response = requests.get(url)
        response.raise_for_status()
        return PullRequest(response.json())


class Client(object):

    def __init__(self, repo, base_branch=None, search_strategy=None):
        self._repo = repo
        self._base_branch = base_branch
        self._search_strategy = search_strategy or PullRequestSearch(repo, 82)

    def pulls_since_last_release(self):
        last_release = self._search_strategy.find()
        cutoff = last_release.closed_at if last_release else None

        pulls = []
        proceed = True
        page_number = 1
        while proceed:
            page = [PullRequest(pull) for pull in self._get_page(page_number)]
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
        return response.json()
