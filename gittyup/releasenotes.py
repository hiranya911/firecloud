import re


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


class _Heading(object):

    NONE = 1
    FCM = 2
    AUTH = 3

    _HEADING_MAP = {
        NONE: '',
        AUTH: '{{auth}}',
        FCM: '{{messaging_longer}}',
    }

    @classmethod
    def text(cls, heading):
        return cls._HEADING_MAP[heading]


_REPLACEMENTS = {
    '{{feature}}': '[Feature]',
    '{{fixed}}': '[Fixed]',
}


class ReleaseNote(object):

    def __init__(self, heading, category, description):
        self.heading = _Heading.text(heading)
        self.category = category
        self.description = description

    def get_devsite_text(self):
        return '{0} {1}'.format(Category.text(self.category), _with_full_stop(self.description))

    def get_github_text(self):
        text = self.get_devsite_text()
        for key, value in _REPLACEMENTS.items():
            text = text.replace(key, value)
        return ReleaseNote.fix_urls(text)

    @classmethod
    def fix_urls(cls, text):
        idx = text.find('](/')
        while idx != -1:
            text = text[:idx + 1] + '(https://firebase.google.com' + text[idx + 2:]
            idx += 25
            idx = text.find('](/', idx)
        return text


class Source(object):

    def get_release_notes(self):
        raise NotImplementedError

    @staticmethod
    def parse_pull_request(pull):
        title_match = ConventionalPullRequestMessage.PATTERN.search(pull.title)
        if title_match:
            return ConventionalPullRequestMessage(
                title_match.group('desc'),
                pull.body,
                title_match.group('type'),
                title_match.group('scope'))

        return PullRequestMessage(pull.title, pull.body)


class PullRequestMessage(Source):

    def __init__(self, title, body):
        self._title = title
        self._body = body

    @property
    def _heading(self):
        return _Heading.NONE

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
          ReleaseNote(self._heading, self._category, _with_full_stop(desc))
          for desc in self._descriptions
        ]


class ConventionalPullRequestMessage(PullRequestMessage):

    PATTERN = re.compile(r'(?P<type>\w+)(\((?P<scope>\w+)\))?:\s+(?P<desc>.+)')

    def __init__(self, title, body, pr_type, scope=None):
        super().__init__(title, body)
        self._type = pr_type
        self._scope = scope

    @property
    def _heading(self):
        if self._scope == 'fcm':
            return _Heading.FCM
        elif self._scope == 'auth':
            return _Heading.AUTH
        else:
            return _Heading.NONE

    @property
    def _category(self):
        category = PullRequestMessage._category.fget(self)
        if category != Category.FIXED:
            return category
        elif self._type == 'feat':
            return Category.FEATURE
        else:
            return Category.FIXED


def get_release_notes_from_pulls(pulls):
    sources = [ Source.parse_pull_request(pull) for pull in pulls ]
    note_lists = [ source.get_release_notes() for source in sources ]
    return [ note for notes in note_lists for note in notes ]


def _with_full_stop(message):
    return message if message.endswith('.') else '{0}.'.format(message)

