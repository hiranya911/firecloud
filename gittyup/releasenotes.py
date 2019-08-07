import datetime
import itertools
import re


_DEFAULT_SECTION = ''
_SECTIONS = {
    'auth': '{{auth}}',
    'fcm': '{{messaging_longer}}'
}

_REPLACEMENTS = {
    '{{feature}}': '[Feature]',
    '{{fixed}}': '[Fixed]',
    '{{messaging_longer}}': 'Firebase Cloud Messaging',
}
_FIRE_SITE_URL = 'https://firebase.google.com'


class Category(object):
    FEATURE = 1
    FIXED = 2
    CHANGED = 3

    @classmethod
    def text(cls, category):
        if category == cls.FEATURE:
            return '{{feature}}'
        elif category == cls.CHANGED:
            return '{{changed}}'
        else:
            return '{{fixed}}'


class ReleaseNote(object):

    def __init__(self, category, description, section=''):
        self.category = category
        self.description = description
        self.section = section

    def get_devsite_text(self):
        desc = _with_full_stop(ReleaseNote._rewrite_url(self.description))
        return '{0} {1}'.format(Category.text(self.category), desc)

    @classmethod
    def _rewrite_url(cls, text):
        marker = ']({0}/'.format(_FIRE_SITE_URL)
        idx = text.find(marker)
        while idx != -1:
            text = text[:idx + 2] + text[idx + 2 + len(_FIRE_SITE_URL):]
            idx = text.find(marker, idx)
        return text


class Source(object):

    def get_release_notes(self):
        raise NotImplementedError

    @staticmethod
    def from_pull_request(pull):
        source = ConventionalPullRequestMessage.from_pull_request(pull)
        if not source:
            source = PullRequestMessage(pull.title, pull.body)

        return source


class PullRequestMessage(Source):

    def __init__(self, title, body):
        self._title = title
        self._body = body

    @property
    def _section(self):
        return _DEFAULT_SECTION

    @property
    def _category(self):
        lines = self._body.splitlines()
        if any([line.startswith('API CHANGE:') for line in lines]):
            return Category.CHANGED
        return Category.FIXED

    @property
    def _descriptions(self):
        lines = self._body.splitlines()
        descs = []
        for line in lines:
            if line.startswith('RELEASE NOTE:'):
                descs.append(line[14:])

        return descs if descs else [ self._title ]

    def get_release_notes(self):
        return [
          ReleaseNote(self._category, _with_full_stop(desc), self._section)
          for desc in self._descriptions
        ]


class ConventionalPullRequestMessage(PullRequestMessage):

    PATTERN = re.compile(r'(?P<type>\w+)(\((?P<scope>\w+)\))?:\s+(?P<desc>.+)')

    def __init__(self, title, body, pr_type, scope=None):
        super().__init__(title, body)
        self._type = pr_type
        self._scope = scope

    @property
    def _section(self):
        return _SECTIONS.get(self._scope, _DEFAULT_SECTION)

    @property
    def _category(self):
        category = PullRequestMessage._category.fget(self)
        if category != Category.FIXED:
            return category
        elif self._type == 'feat':
            return Category.FEATURE
        else:
            return Category.FIXED

    @staticmethod
    def from_pull_request(pull):
        title_match = ConventionalPullRequestMessage.PATTERN.search(pull.title)
        if title_match:
            return ConventionalPullRequestMessage(
                title_match.group('desc'),
                pull.body,
                title_match.group('type'),
                title_match.group('scope'))
        return None


def get_release_notes_from_pulls(pulls):
    sources = [ Source.from_pull_request(pull) for pull in pulls ]
    note_lists = [ source.get_release_notes() for source in sources ]
    return [ note for notes in note_lists for note in notes ]


def _with_full_stop(message):
    return message if message.endswith('.') else '{0}.'.format(message)

def _group_by_section(notes):
    grouped_notes = {}
    for key, group in itertools.groupby(notes, lambda p : p.section):
        if key not in grouped_notes:
            grouped_notes[key] = []
        for note in group:
            grouped_notes[key].append(note)
    return grouped_notes


def generate_for_devsite(notes):
    grouped_notes = _group_by_section(notes)

    result = ''
    for key in sorted(grouped_notes.keys()):
        if key:
            result += '### {0}\n\n'.format(key)

        for commit in grouped_notes[key]:
            note = commit.get_devsite_text()
            result += '- {0}\n'.format(note)
        result += '\n'
    return result


def get_github_text(text):
    for key, value in _REPLACEMENTS.items():
        text = text.replace(key, value)
    return _fix_urls(text)


def _fix_urls(text):
    idx = text.find('](/')
    while idx != -1:
        text = text[:idx + 2] + _FIRE_SITE_URL + text[idx + 2:]
        idx += len(_FIRE_SITE_URL)
        idx = text.find('](/', idx)
    return text


def estimate_next_version(last_version, notes):
    major, minor, patch = last_version.major, last_version.minor, last_version.patch
    if any([note.category == Category.CHANGED for note in notes]):
        major += 1
    elif any([note.category == Category.FEATURE for note in notes]):
        minor += 1
    else:
        patch += 1
    return '{0}.{1}.{2}'.format(major, minor, patch)


def estimate_release_date():
    today = datetime.datetime.now()
    tomorrow = today + datetime.timedelta(days=1)
    return tomorrow.strftime('%d %B, %Y')