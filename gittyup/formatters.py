import datetime
import itertools
import textwrap

import releasenotes


_FIRE_SITE_URL = 'https://firebase.google.com'


class ReleaseNoteFormatter(object):

    def header(self):
        raise NotImplementedError

    def format_note(self, note):
        raise NotImplementedError

    def format_section_header(self, title):
        raise NotImplementedError

    def format_section_footer(self, title):
        raise NotImplementedError

    def printable_output(self, notes):
        grouped_notes = ReleaseNoteFormatter._group_by_section(notes)

        result = self.header()
        for title in sorted(grouped_notes.keys()):
            if title:
                result += self.format_section_header(title)

            for note in grouped_notes[title]:
                note_text = self.format_note(note)
                result += '- {0}'.format(note_text)
            result += self.format_section_footer(title)
        return result

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

    def __init__(self, next_version):
        self._next_version = next_version

    def header(self):
        release_date = DevsiteFormatter._estimate_release_date()
        return '## <a name="{0}">Version {0} - {1}</a>\n\n'.format(self._next_version, release_date)

    def format_note(self, note):
        note_type = DevsiteFormatter._note_type(note.type)
        desc = _with_full_stop(DevsiteFormatter._ensure_relative_urls(note.description))
        result = '{0} {1}'.format(note_type, desc)
        return DevsiteFormatter._wrap(result)

    def format_section_header(self, title):
        title_markdown = DevsiteFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown  )

    def format_section_footer(self, title):
        return '\n'

    @classmethod
    def _note_type(cls, note_type):
      if note_type == releasenotes.NoteType.FEATURE:
        return '{{feature}}'
      elif note_type == releasenotes.NoteType.CHANGED:
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

    def __init__(self, next_version):
        self._next_version = next_version

    def header(self):
        return '{0}\n\n'.format(self._next_version)

    def format_note(self, note):
        note_type = GitHubFormatter._note_type(note.type)
        desc = _with_full_stop(GitHubFormatter._ensure_absolute_urls(note.description))
        return '{0} {1}\n'.format(note_type, desc)

    def format_section_header(self, title):
        title_markdown = GitHubFormatter._SECTIONS.get(title, title)
        return '### {0}\n\n'.format(title_markdown)

    def format_section_footer(self, title):
        return '\n'

    @classmethod
    def _note_type(cls, note_type):
      if note_type == releasenotes.NoteType.FEATURE:
        return '[Feature]'
      elif note_type == releasenotes.NoteType.CHANGED:
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
