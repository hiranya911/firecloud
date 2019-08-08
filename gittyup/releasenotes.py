import re


_DEFAULT_SECTION = ''


class NoteType(object):
    FEATURE = 1
    FIXED = 2
    CHANGED = 3


class Attribution(object):

    def __init__(self, pull):
        self.user = pull.user
        self.url = pull.url


class ReleaseNote(object):

    def __init__(self, note_type, description, section='', attribution=None):
        self.type = note_type
        self.description = description
        self.section = section
        self.attribution = attribution

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


class PullRequestMessage(Source):

    _API_CHANGE = 'API CHANGE:'
    _RELEASE_NOTE = 'RELEASE NOTE:'

    def __init__(self, pull):
        self._pull = pull
        self._body = pull.body
        self.title = pull.title

    @property
    def section(self):
        return _DEFAULT_SECTION

    @property
    def note_type(self):
        lines = self._body.splitlines()
        if any([line.startswith(PullRequestMessage._API_CHANGE) for line in lines]):
            return NoteType.CHANGED
        return NoteType.FIXED

    @property
    def _descriptions(self):
        lines = self._body.splitlines()
        descs = []
        for line in lines:
            if line.startswith(PullRequestMessage._RELEASE_NOTE):
                descs.append(line[len(PullRequestMessage._RELEASE_NOTE):].strip())
            if line.startswith(PullRequestMessage._API_CHANGE):
                descs.append(line[len(PullRequestMessage._API_CHANGE):].strip())

        return descs if descs else [ self.title ]

    def get_release_notes(self):
        attribution = Attribution(self._pull) if self._pull.is_contribution else None
        return [
          ReleaseNote(self.note_type, desc, self.section, attribution)
          for desc in self._descriptions
        ]


class ConventionalPullRequestMessage(PullRequestMessage):

    PATTERN = re.compile(r'(?P<type>\w+)(\((?P<scope>\w+)\))?:\s+(?P<desc>.+)')

    def __init__(self, pull, title, pr_type, scope=None):
        super().__init__(pull)
        self.title = title
        self._pr_type = pr_type
        self._scope = scope

    @property
    def section(self):
        return self._scope or _DEFAULT_SECTION

    @property
    def note_type(self):
        note_type = PullRequestMessage.note_type.fget(self)
        if note_type != NoteType.FIXED:
            return note_type
        elif self._pr_type == 'feat':
            return NoteType.FEATURE
        else:
            return NoteType.FIXED

    @classmethod
    def from_pull_request(cls, pull):
        title_match = cls.PATTERN.search(pull.title)
        if title_match:
            return ConventionalPullRequestMessage(
                pull,
                title_match.group('desc'),
                title_match.group('type'),
                title_match.group('scope'))
        return None


def find_next_version(last_version, notes):
    if not last_version:
        raise ValueError('last_version must be specified')

    major, minor, patch = last_version.segments
    if any([note.is_change for note in notes]):
        major += 1
    elif any([note.is_feature for note in notes]):
        minor += 1
    else:
        patch += 1
    return '{0}.{1}.{2}'.format(major, minor, patch)


def _source_from_pull_request(pull):
    source = ConventionalPullRequestMessage.from_pull_request(pull)
    if not source:
        source = PullRequestMessage(pull)

    return source


def get_release_notes_from_pull(pull):
    source = _source_from_pull_request(pull)
    return source.get_release_notes()
