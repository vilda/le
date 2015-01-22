
# coding: utf-8
# vim: set ts=4 sw=4 et:

__author__ = 'Logentries'

__all__ = ['FormatPlain', 'FormatSyslog']


import datetime
import socket


class FormatPlain(object):

    """Formats lines as plain text, prepends each line with token."""

    def __init__(self, token):
        self._token = token

    def format_line(self, line):
        return self._token + line


class FormatSyslog(object):

    """Formats lines according to Syslog format RFC 5424. Hostname is taken
    from configuration or current hostname is used."""

    def __init__(self, hostname, appname, token):
        if hostname:
            self._hostname = hostname
        else:
            self._hostname = socket.gethostname()
        self._appname = appname
        self._token = token

    def format_line(self, line):
        return '%s<14>1 %sZ hotname=%s appname=%s - - - %s' % (self._token,
                datetime.datetime.utcnow().isoformat('T'), self._hostname,
                self._appname, line)

    def format_line_ext(self, msgid, line):
        return '%s<14>1 %sZ hostname=%s appname=%s - msgid=%s - %s' % (self._token,
                datetime.datetime.utcnow().isoformat('T'), self._hostname,
                self._appname, msgid, line)
