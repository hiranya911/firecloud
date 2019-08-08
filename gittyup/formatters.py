import datetime
import itertools
import textwrap


_FIRE_SITE_URL = 'https://firebase.google.com'


class ReleaseNoteFormatter(object):

    def __init__(self, notes, last_version=None, next_version=None):
        self.notes = notes
        self._last_version = last_version
        self._next_version = next_version

    def header(self):
        raise NotImplementedError

    def format_note(self, note):
        raise NotImplementedError

    def format_section_header(self, title):
        raise NotImplementedError

    def format_section_footer(self, title):
        raise NotImplementedError

    def printable_output(self):
        grouped_notes = ReleaseNoteFormatter._group_by_section(self.notes)

        result = self.header()
        for title in sorted(grouped_notes.keys()):
            if title:
                result += self.format_section_header(title)

            for note in grouped_notes[title]:
                note_text = self.format_note(note)
                result += '- {0}'.format(note_text)
            result += self.format_section_footer(title)
        return result

    def _find_next_version(self):
        if self._next_version:
            return self._next_version
        if not self._last_version:
            raise ValueError('Either next_version or last_version must be specified')

        major, minor, patch = self._last_version.major, self._last_version.minor, self._last_version.patch
        if any([note.is_change for note in self.notes]):
            major += 1
        elif any([note.is_feature for note in self.notes]):
            minor += 1
        else:
            patch += 1
        return '{0}.{1}.{2}'.format(major, minor, patch)


    @classmethod
    def _group_by_section(cls, notes):
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

    def __init__(self, notes, last_version):
        super().__init__(notes, last_version)

    def header(self):
        next_version = self._find_next_version()
        release_date = DevsiteFormatter._estimate_release_date()
        return '## <a name="{0}">Version {0} - {1}</a>\n\n'.format(next_version, release_date)

    def format_note(self, note):
        note_type = DevsiteFormatter._note_type(note)
        desc = _with_full_stop(DevsiteFormatter._ensure_relative_urls(note.description))
        kudos = _attribution_text(note)
        result = '{0} {1} {2}'.format(note_type, desc, kudos)
        return DevsiteFormatter._wrap(result)

    def format_section_header(self, title):
        title_markdown = DevsiteFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown  )

    def format_section_footer(self, title):
        return '\n'

    @classmethod
    def _note_type(cls, note):
      if note.is_feature:
        return '{{feature}}'
      elif note.is_change:
          return '{{changed}}'
      else:
          return '{{fixed}}'

    @classmethod
    def _ensure_relative_urls(cls, text):
        marker = ']({0}/'.format(_FIRE_SITE_URL)
        idx = text.find(marker)
        while idx != -1:
            text = text[:idx + 2] + text[idx + 2 + len(_FIRE_SITE_URL):]
            idx = text.find(marker, idx)
        return text

    @classmethod
    def _estimate_release_date(cls):
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime('%d %B, %Y')

    @classmethod
    def _ensure_relative_urls(cls, text):
        marker = ']({0}/'.format(_FIRE_SITE_URL)
        idx = text.find(marker)
        while idx != -1:
            text = text[:idx + 2] + text[idx + 2 + len(_FIRE_SITE_URL):]
            idx = text.find(marker, idx)
        return text

    @classmethod
    def _wrap(cls, line, max_length=80):
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

    def format_note(self, note):
        note_type = GitHubFormatter._note_type(note)
        desc = _with_full_stop(GitHubFormatter._ensure_absolute_urls(note.description))
        kudos = _attribution_text(note)
        return '{0} {1} {2}\n'.format(note_type, desc, kudos)

    def format_section_header(self, title):
        title_markdown = GitHubFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown)

    def format_section_footer(self, title):
        return '\n'

    @classmethod
    def _note_type(cls, note):
      if note.is_feature:
        return '[Feature]'
      elif note.is_change:
          return '[Changed]'
      else:
          return '[Fixed]'

    @classmethod
    def _ensure_absolute_urls(cls, text):
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
