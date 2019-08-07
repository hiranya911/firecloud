import re


_DEFAULT_SECTION = ''


class NoteType(object):
    FEATURE = 1
    FIXED = 2
    CHANGED = 3


class ReleaseNote(object):

    def __init__(self, note_type, description, section=''):
        self.type = note_type
        self.description = description
        self.section = section

    @property
    def is_feature(self):
        return self.type == NoteType.FEATURE

    @property
    def is_fix(self):
        return self.type == NoteType.FIXED

    @property
    def is_change(self):
        return self.type == NoteType.CHANGED


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
    def _type(self):
        lines = self._body.splitlines()
        if any([line.startswith('API CHANGE:') for line in lines]):
            return NoteType.CHANGED
        return NoteType.FIXED

    @property
    def _descriptions(self):
        lines = self._body.splitlines()
        descs = []
        for line in lines:
            if line.startswith('RELEASE NOTE:'):
                descs.append(line[14:].strip())

        return descs if descs else [ self._title ]

    def get_release_notes(self):
        return [
          ReleaseNote(self._type, desc, self._section)
          for desc in self._descriptions
        ]


class ConventionalPullRequestMessage(PullRequestMessage):

    PATTERN = re.compile(r'(?P<type>\w+)(\((?P<scope>\w+)\))?:\s+(?P<desc>.+)')

    def __init__(self, title, body, pr_type, scope=None):
        super().__init__(title, body)
        self._pr_type = pr_type
        self._scope = scope

    @property
    def _section(self):
        return self._scope or _DEFAULT_SECTION

    @property
    def _type(self):
        note_type = PullRequestMessage._type.fget(self)
        if note_type != NoteType.FIXED:
            return note_type
        elif self._pr_type == 'feat':
            return NoteType.FEATURE
        else:
            return NoteType.FIXED

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


def get_release_notes_from_pull(pull):
    source = Source.from_pull_request(pull)
    return source.get_release_notes()
