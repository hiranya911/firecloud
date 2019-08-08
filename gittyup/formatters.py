import datetime
import itertools
import textwrap


_FIRE_SITE_URL = 'https://firebase.google.com'


class ReleaseNoteFormatter(object):

    def __init__(self, notes, last_version=None, next_version=None):
        self._notes = notes
        self._last_version = last_version
        self._next_version = next_version

    def header(self):
        raise NotImplementedError

    def note(self, note):
        raise NotImplementedError

    def section_header(self, title):
        raise NotImplementedError

    def section_footer(self, title):
        raise NotImplementedError

    def printable_output(self):
        grouped_notes = ReleaseNoteFormatter._group_by_section(self._notes)

        result = self.header()
        for title in sorted(grouped_notes.keys()):
            if title:
                result += self.section_header(title)

            for note in grouped_notes[title]:
                note_text = self.note(note)
                result += '- {0}'.format(note_text)
            result += self.section_footer(title)
        return result

    def _find_next_version(self):
        if self._next_version:
            return self._next_version
        if not self._last_version:
            raise ValueError('Either next_version or last_version must be specified')

        major, minor, patch = self._last_version.segments
        if any([note.is_change for note in self._notes]):
            major += 1
        elif any([note.is_feature for note in self._notes]):
            minor += 1
        else:
            patch += 1
        return '{0}.{1}.{2}'.format(major, minor, patch)

    @staticmethod
    def _group_by_section(notes):
        grouped_notes = {}
        for key, group in itertools.groupby(notes, lambda p : p.section):
            if key not in grouped_notes:
                grouped_notes[key] = []
            for note in group:
                grouped_notes[key].append(note)
        return grouped_notes


class DevsiteFormatter(ReleaseNoteFormatter):

    _SECTIONS = {
        'auth': '{{auth}}',
        'fcm': '{{messaging_longer}}'
    }
    _DATE_FORMAT = '%d %B, %Y'

    def __init__(self, notes, last_version, release_date=None):
        super().__init__(notes, last_version)
        self._release_date = release_date

    def header(self):
        next_version = self._find_next_version()
        release_date = self._estimate_release_date()
        return '## <a name="{0}">Version {0} - {1}</a>\n\n'.format(next_version, release_date)

    def note(self, note):
        note_type = DevsiteFormatter._note_type(note)
        desc = _with_full_stop(DevsiteFormatter._ensure_relative_urls(note.description))
        kudos = _attribution_text(note)
        result = '{0} {1}{2}'.format(note_type, desc, kudos)
        return DevsiteFormatter._wrap(result)

    def section_header(self, title):
        title_markdown = DevsiteFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown  )

    def section_footer(self, title):
        return '\n'

    def _estimate_release_date(self):
        if self._release_date:
            return self._release_date.strftime(DevsiteFormatter._DATE_FORMAT)
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime(DevsiteFormatter._DATE_FORMAT)

    @staticmethod
    def _note_type(note):
      if note.is_feature:
        return '{{feature}}'
      elif note.is_change:
          return '{{changed}}'
      else:
          return '{{fixed}}'

    @staticmethod
    def _ensure_relative_urls(text):
        marker = ']({0}/'.format(_FIRE_SITE_URL)
        idx = text.find(marker)
        while idx != -1:
            text = text[:idx + 2] + text[idx + 2 + len(_FIRE_SITE_URL):]
            idx = text.find(marker, idx)
        return text

    @staticmethod
    def _ensure_relative_urls(text):
        marker = ']({0}/'.format(_FIRE_SITE_URL)
        idx = text.find(marker)
        while idx != -1:
            text = text[:idx + 2] + text[idx + 2 + len(_FIRE_SITE_URL):]
            idx = text.find(marker, idx)
        return text

    @staticmethod
    def _wrap(line, max_length=80):
      if len(line) <= max_length:
          return '{0}\n'.format(line)

      wrapped = textwrap.wrap(line, max_length, break_long_words=False, break_on_hyphens=False)
      indented = [ '  {0}'.format(part) for part in wrapped[1:] ]
      return '{0}\n'.format('\n'.join([wrapped[0]] + indented))


class GitHubFormatter(ReleaseNoteFormatter):

    _SECTIONS = {
        'auth': 'Authentication',
        'fcm': 'Cloud Messaging'
    }

    def __init__(self, notes, last_version):
      super().__init__(notes, last_version)

    def header(self):
        next_version = self._find_next_version()
        return '{0}\n\n'.format(next_version)

    def note(self, note):
        note_type = GitHubFormatter._note_type(note)
        desc = _with_full_stop(GitHubFormatter._ensure_absolute_urls(note.description))
        kudos = _attribution_text(note)
        return '{0} {1}{2}\n'.format(note_type, desc, kudos)

    def section_header(self, title):
        title_markdown = GitHubFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown)

    def section_footer(self, title):
        return '\n'

    @staticmethod
    def _note_type(note):
      if note.is_feature:
        return '[Feature]'
      elif note.is_change:
          return '[Changed]'
      else:
          return '[Fixed]'

    @staticmethod
    def _ensure_absolute_urls(text):
        idx = text.find('](/')
        while idx != -1:
            text = text[:idx + 2] + _FIRE_SITE_URL + text[idx + 2:]
            idx += len(_FIRE_SITE_URL)
            idx = text.find('](/', idx)
        return text


def _with_full_stop(message):
    return message if message.endswith('.') else '{0}.'.format(message)


def _attribution_text(note):
  kudos = note.attribution
  if kudos:
      return ' Thanks [{0}]({1}) for the [contribution]({2}).'.format(
        kudos.user.login, kudos.user.url, kudos.url)

  return ''


def truncate_or_pad(string, length):
    diff = len(string) - length
    if diff > 0:
        string = string[:length - 3] + '...'
    elif diff < 0:
        string = string + ' ' * abs(diff)
    return string
