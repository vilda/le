
# coding: utf-8
# ex: set tabstop=4 shiftwidth=4 expandtab

__author__ = 'Logentries'

__all__ = ['FormatPlain', 'FormatSyslog']


import datetime
import socket


class FormatPlain(object):
    """Formats lines as plain text, prepends each line with token."""

    def __init__(self, token):
        self.token = token

    def format_line(self, line):
        return self.token + line

class FormatSyslog(object):
    """Formats lines according to Syslog format RFC 5424. Hostname is taken
    from configuration or current hostname is used."""

    def __init__(self, hostname, appname):
        if hostname:
            self._hostname = hostname
        else:
            self._hostname = socket.gethostname()
        self._appname = appname

    def format_line(self, line):
        return '<14>1 %sZ %s %s - - - %s' % (datetime.datetime.utcnow().isoformat('T'),
                self._hostname, self._appname, line)

