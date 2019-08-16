import datetime

import requests


_GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Cutoff(object):

    def get_datetime(self):
        raise NotImplementedError()

    def get_description(self):
        raise NotImplementedError()


class User(object):

    def __init__(self, data):
        self._data = data

    @property
    def login(self):
        return self._data['login']

    @property
    def url(self):
        return self._data['html_url']


class PullRequest(Cutoff):

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
            self._data['updated_at'], _GITHUB_DATE_FORMAT)

    @property
    def closed_at(self):
        return datetime.datetime.strptime(
            self._data['closed_at'], _GITHUB_DATE_FORMAT)

    def get_datetime(self):
        return self.closed_at

    def get_description(self):
        return 'PR: [{0}] {1}'.format(self.number, self.title)


class Commit(Cutoff):

    def __init__(self, data):
        self._data = data

    @property
    def message(self):
        return self._data['commit']['message']

    def get_datetime(self):
        date = self._data['commit']['committer']['date']
        return datetime.datetime.strptime(date, _GITHUB_DATE_FORMAT)

    def get_description(self):
        return 'Commit: [{0}...] {1}'.format(self._data['sha'][:5], self.message)


class Release(object):

    def __init__(self, data):
        self._data = data

    @property
    def tag_name(self):
        return self._data['tag_name']

    @property
    def published_at(self):
        return datetime.datetime.strptime(
            self._data['published_at'], _GITHUB_DATE_FORMAT)

    @property
    def version(self):
        version = self.tag_name
        if version.startswith('v'):
            version = version[1:]
        return version


class CutoffSearchStrategy(object):

    def search(self, client):
        raise NotImplementedError


class SearchByPullRequestTitle(CutoffSearchStrategy):

    def __init__(self, prefix):
        self._prefix = prefix

    def search(self, client):
        query = [
            'repo:{0}'.format(client.repo),
            'is:pr',
            'state:closed',
            '{0}:in:title'.format(self._prefix),
        ]
        if client.base_branch:
            query.append('base:{0}'.format(client.base_branch))

        url = 'https://api.github.com/search/issues?q={0}'.format('+'.join(query))
        params = {
            'sort': 'updated',
            'direction': 'desc',
        }

        response = requests.get(url, params=params, headers=client.auth)
        response.raise_for_status()
        body = response.json()
        if body.get('total_count', 0) > 0:
            items = body.get('items')
            return PullRequest(items[0])
        return None

    def __str__(self):
        return 'pull request with: {{ TitlePrefix = "{0}" }}'.format(self._prefix)


class SearchByPullRequestNumber(CutoffSearchStrategy):

    def __init__(self, number):
        self._number = number

    def search(self, client):
        url = 'https://api.github.com/repos/{0}/pulls/{1}'.format(client.repo, self._number)
        response = requests.get(url, headers=client.auth)
        response.raise_for_status()
        return PullRequest(response.json())

    def __str__(self):
        return 'pull request with: {{ Number = {0} }}'.format(self._number)


class SearchByCommitMessage(CutoffSearchStrategy):

    def __init__(self, prefix):
        self._prefix = prefix

    def search(self, client):
        url = 'https://api.github.com/repos/{0}/commits'.format(client.repo)
        params = {}
        if client.base_branch:
            params['sha'] = client.base_branch

        page_number = 1
        while True:
            page = self._get_page(client, page_number)
            if not page:
                break

            for commit in page:
                if commit.message.startswith(self._prefix):
                    return commit
            page_number += 1
        return None

    def _get_page(self, client, page_number=1):
        url = 'https://api.github.com/repos/{0}/commits'.format(client.repo)
        params = {
            'page': page_number,
        }
        if client.base_branch:
            params['sha'] = client.base_branch

        response = requests.get(url, params=params, headers=client.auth)
        response.raise_for_status()
        return [ Commit(c) for c in response.json() ]

    def __str__(self):
        return 'commit with: {{ MessagePrefix = "{0}" }}'.format(self._prefix)


class SearchByCommitSha(CutoffSearchStrategy):

    def __init__(self, sha):
        self._sha = sha

    def search(self, client):
        url = 'https://api.github.com/repos/{0}/commits/{1}'.format(client.repo, self._sha)
        response = requests.get(url, headers=client.auth)
        response.raise_for_status()
        return Commit(response.json())

    def __str__(self):
        return 'commit with: {{ Sha = "{0}" }}'.format(self._sha)


class Client(object):

    def __init__(self, repo, base_branch=None, token=None):
        self.repo = repo
        self.base_branch = base_branch
        self._token = token

    @property
    def auth(self):
        if self._token:
            return {'Authorization': 'token {0}'.format(self._token)}
        return None

    def find_pulls_since(self, cutoff=None):
        cutoff_datetime = cutoff.get_datetime() if cutoff else None

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
                if cutoff_datetime and pull.updated_at < cutoff_datetime:
                    proceed = False
                    break
                filtered.append(pull)
            pulls.extend(filtered)
            page_number += 1

        if cutoff_datetime:
            pulls = [pull for pull in pulls if pull.closed_at > cutoff_datetime]

        return sorted(pulls, key=lambda p: p.closed_at)

    def find_last_release(self):
        url = 'https://api.github.com/repos/{0}/releases'.format(self.repo)
        response = requests.get(url, headers=self.auth)
        response.raise_for_status()
        releases = response.json()
        if releases:
            return Release(response.json()[0])
        return None

    def find_last_release_version(self):
        release = self.find_last_release()
        if not release:
            return (0, 0, 0)

        tag_name = release.tag_name
        if tag_name.startswith('v'):
            tag_name = tag_name[1:]
        return tuple([ int(x) for x in tag_name.split('.') ])

    def _get_page(self, page_number=1):
        url = 'https://api.github.com/repos/{0}/pulls'.format(self.repo)
        params = {
            'state': 'closed',
            'page': page_number,
            'sort': 'updated',
            'direction': 'desc',
        }
        if self.base_branch:
            params['base'] = self.base_branch

        response = requests.get(url, params=params, headers=self.auth)
        response.raise_for_status()
        return [ PullRequest(p) for p in response.json() ]
