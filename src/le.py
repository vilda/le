#!/usr/bin/env python2
# coding: utf-8

#
# Logentries agent <https://logentries.com/>.

#
# Constants
#
from utils import *

VERSION = "1.4.0"

NOT_SET = None

# Default user and agent keys of none are defined in configuration
DEFAULT_USER_KEY = NOT_SET
DEFAULT_AGENT_KEY = NOT_SET

# Configuration files
CONFIG_DIR_SYSTEM = '/etc/le'
CONFIG_DIR_USER = '.le'
LE_CONFIG = 'config'

PID_FILE = '/var/run/logentries.pid'

MAIN_SECT = 'Main'
USER_KEY_PARAM = 'user-key'
AGENT_KEY_PARAM = 'agent-key'
FILTERS_PARAM = 'filters'
SUPPRESS_SSL_PARAM = 'suppress_ssl'
USE_CA_PROVIDED_PARAM = 'use_ca_provided'
FORCE_DOMAIN_PARAM = 'force_domain'
DATAHUB_PARAM = 'datahub'
SYSSTAT_TOKEN_PARAM = 'system-stat-token'
KEY_LEN = 36
ACCOUNT_KEYS_API = '/agent/account-keys/'
ID_LOGS_API = '/agent/id-logs/'


# Logentries server details
LE_SERVER_API = '/'

LE_DEFAULT_SSL_PORT = 20000
LE_DEFAULT_NON_SSL_PORT = 10000

SYSTEM_STATS_TAG = 'SystemStats'
SYSTEM_STATS_LOG_FILE = SYSTEM_STATS_TAG + '.log'


class Domain(object):
    """ Logentries domains. """
    # General domains
    MAIN = 'logentries.com'
    API = 'api.logentries.com'
    DATA = 'api.logentries.com'  # TODO
    PULL = 'pull.logentries.com'
    STREAM = 'data.logentries.com'
    # Local debugging
    MAIN_LOCAL = 'localhost:8000'
    API_LOCAL = 'localhost:8081'
    DATA_LOCAL = 'localhost:8081'


CONTENT_LENGTH = 'content-length'

# Log root directory
LOG_ROOT = '/var/log'

# Timeout after server connection fail. Might be a temporary network
# failure.
SRV_RECON_TIMEOUT = 10  # in seconds

# Timeout after invalid server response. Might be a version mishmash or
# temporary server/network failure
INV_SRV_RESP_TIMEOUT = 30  # Seconds

# Time interval between re-trying to open log file
REOPEN_TRY_INTERVAL = 1  # Seconds

# Number of lines which can be sent in one buck, piggybacking
MAX_LINES_SENT = 10

# Time in seconds spend between log re-checks
TAIL_RECHECK = 0.2  # Seconds

# Number of attemps to read a file, until the name is recheck
NAME_CHECK = 4  # TAIL_RECHECK cycles

# Number of read line false attemps between are-you-alive packets
IAA_INTERVAL = 100
IAA_TOKEN = "###LE-IAA###\n"

# Maximal size of a block of events
MAX_EVENTS = 65536

# Interval between attampts to open a file
REOPEN_INT = 1  # Seconds

# Linux block devices
SYS_BLOCK_DEV = '/sys/block/'
# Linux CPU stat file
CPUSTATS_FILE = '/proc/stat'
# Linux mmeory stat file
MEMSTATS_FILE = '/proc/meminfo'
# Linux network stat file
NETSTATS_FILE = '/proc/net/dev'

# List of accepted network devices
NET_DEVICES = ['  eth', ' wlan', 'venet', ' veth']

EPOCH = 5  # in seconds

QUEUE_WAIT_TIME = 1  # time in seconds to wait for reading from the transport queue if it is empty


# File Handler Positions
FILE_BEGIN = 0
FILE_CURRENT = 1
FILE_END = 2

# Config response parameters
CONF_RESPONSE = 'response'
CONF_REASON = 'reason'
CONF_LOGS = 'logs'
CONF_SERVERS = 'servers'
CONF_OK = 'ok'

# Server requests
RQ_WORKLOAD = 'push_wl'

# Release information on LSB systems
LSB_RELEASE = '/etc/lsb-release'



#
# Usage help
#

PULL_USAGE = "pull <path> <when> <filter> <limit>"
PUSH_USAGE = "push <file> <path> <log-type>"
USAGE = "Logentries agent version " + VERSION + """
usage: le.py COMMAND [ARGS]

Where command is one of:
  init      Write local configuration file
  reinit    As init but does not reset undefined parameters
  register  Register this host
    --name=  name of the host
    --hostname=  hostname of the host
  whoami    Displays settings for this host
  monitor   Monitor this host
  follow <filename>  Follow the given log
    --name=  name of the log
    --type=  type of the log
  followed <filename>  Check if the file is followed
  clean     Removes configuration file
  ls        List internal filesystem and settings: <path>
  rm        Remove entity: <path>
  pull      Pull log file: <path> <when> <filter> <limit>

Where parameters are:
  --help               show usage help and exit
  --version            display version number and exit
  --account-key=       set account key and exit
  --host-key=          set local host key and exit, generate key if key is empty
  --no-timestamps      no timestamps in agent reportings
  --force              force given operation
  --suppress-ssl       do not use SSL with API server
  --yes                always respond yes
  --datahub            send logs to the specified data hub address
                       the format is address:port with port being optional
  --system-stat-token= set the token for system stats log (beta)
"""


# Global indicator of monitoring interruption
shutdown = False


def set_shutdown():
    global shutdown
    shutdown = True
    print >> sys.stderr, "Shutting down"


def report(what):
    print >> sys.stderr, what


def print_usage(version_only=False):
    if version_only:
        report(VERSION)
    else:
        report(USAGE)

    sys.exit(EXIT_HELP)


#
# Libraries
#

import string
import re
import ConfigParser
import fileinput
import getopt
import glob
import logging
import os
import os.path
import platform
import socket
import subprocess
import traceback
import sys
import threading
import time
import datetime
import urllib
import urllib2
import httplib
import getpass
import atexit
import logging.handlers
from collections import deque
from backports import CertificateError, match_hostname
#
# Start logging
#

log = logging.getLogger(LOG_LE_AGENT)
if not log:
    report("Cannot open log output")
    sys.exit(EXIT_ERR)

log.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(stream_handler)


class StatisticsSendingWorker(threading.Thread):
    """
    Class that is used for sending statistics over TCP stream (Token-based).
    Must receive message queue reference in constructor
    and reference to transport provider. Works as separate thread
    just grabbing a message from the queue and pushing it to transport provider.
    """

    def __init__(self, stats_tcp_transport, msg_queue):
        threading.Thread.__init__(self)
        self.msg_queue = msg_queue
        self.transport = stats_tcp_transport

    def run(self):
        while True:
            try:
                msg = self.msg_queue.popleft()
                self.transport.send(msg)
            except IndexError:
                time.sleep(QUEUE_WAIT_TIME)


# Logic of SSLSysLogHandler class is based on code from
# https://raw.githubusercontent.com/lhl/python-syslogssl/master/syslogssl.py
# with several modifications.

class SSLSysLogHandler(logging.handlers.SysLogHandler):
    def __init__(self, address, port, use_ssl=True, certs=None,
                 facility=logging.handlers.SysLogHandler.LOG_USER):
        logging.handlers.SysLogHandler.__init__(self)
        self.address = address
        self.facility = facility
        self.port = port
        self.use_ssl = use_ssl
        self.certs = certs
        self.socket = NOT_SET

        try:
            self.reconnect()
        except Exception, e:
            report("Encountered unexpected exception: %s - continuing" % e.message)
            raise e

    def close(self):
        if not self.socket is None:
            self.socket.close()
        logging.handlers.SysLogHandler.close(self)

    def emit(self, record):
        msg = self.format(record)
        prio = '<%d>' % self.encodePriority(self.facility,
                                            self.mapPriority(record.levelname))
        if type(msg) is unicode:
            msg = msg.encode('utf-8')
        msg = prio + msg
        try:
            self.socket.sendall(msg)
        except (IOError, AttributeError):
            report("Unable to send message to %s:%s. Make sure the service is available." % (self.address,
                                                                                                self.port))
            report("Trying to reconnect...")

            try:
                self.reconnect()
                self.socket.send(msg)
                report("Reconnection was successful, the message has been sent.")
            except (AttributeError, ValueError, IOError):
                pass
        except(KeyboardInterrupt, SystemExit):
            raise
        except IOError:
            pass
        except:
            self.handleError(record)

    def connect_ssl(self, plain_socket):
        try:
            try:
                self.socket = ssl.wrap_socket(plain_socket, ca_certs=self.certs, cert_reqs=ssl.CERT_REQUIRED,
                                              ssl_version=ssl.PROTOCOL_TLSv1,
                                              ciphers="HIGH:-aNULL:-eNULL:-PSK:RC4-SHA:RC4-MD5")
            except TypeError:
                self.socket = ssl.wrap_socket(plain_socket, ca_certs=self.certs, cert_reqs=ssl.CERT_REQUIRED,
                                              ssl_version=ssl.PROTOCOL_TLSv1)

            self.socket.connect((self.address, self.port))

            try:
                match_hostname(self.socket.getpeercert(), self.address)
            except CertificateError, ce:
                die("Could not validate SSL certificate for %s: %s" % (self.address, ce.message))


        except IOError, e:
            cause = e.strerror
            if not cause:
                cause = ""
            report("Can't connect to %s via SSL at port %s. Make sure that the host and port are reachable "
                   "and speak SSL: %s" % (self.address, self.port, cause))

            self.socket.close()
            self.socket = None

    def connect_insecure(self, plain_socket):
        try:
            self.socket = plain_socket
            self.socket.connect((self.address, self.port))
        except IOError, e:
            cause = e.strerror
            if not cause:
                cause = ""
            report("Can't connect to %s via plaintext at port %s. Make sure that the host and port are reachable\n"
                   "Error message: %s" % (self.address, self.port, e.strerror))

            self.socket.close()
            self.socket = None


    def reconnect(self):
        try:
            if not self.socket is None:
                self.socket.close()
                self.socket = None
        except:
            pass

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TCP_TIMEOUT)

        if self.use_ssl:
            self.connect_ssl(s)
        else:
            self.connect_insecure(s)


class StreamLogSender(object):
    """
    Class that is used to format system stats messages to Syslog format
    and send to LE service using TCP stream handler
    """

    def __init__(self, tag, address, port, use_ssl, cert_name):
        self.logger = logging.getLogger(tag)
        self.logger.setLevel(logging.INFO)
        self.handler = SSLSysLogHandler(address, port, use_ssl, cert_name)
        self.handler.setLevel(logging.DEBUG)
        log_format = "%(asctime)s {0} {1}: %(message)s\r\n".format(config.hostname_required(), tag.replace(' ', '_'))
        time_format = "%Y-%m-%dT%H:%M:%SZ"
        log_formatter = logging.Formatter(log_format, time_format)
        log_formatter.converter = time.gmtime
        self.handler.setFormatter(log_formatter)
        self.logger.addHandler(self.handler)

    def send(self, msg):
        self.logger.info(msg)


class SyslogStreamSender(object):
    """
    Class that encapsulates both transport and message sending worker.
    Used to send system stats messages to LE service in non-Syslog mode
    e.g. not using DataHub.
    """

    def __init__(self, tag=SYSTEM_STATS_TAG, endpoint_address=Domain.STREAM,
                 port=LE_DEFAULT_SSL_PORT, use_ssl=True):
        self.msg_queue = deque(maxlen=10000)
        self.endpoint_address = endpoint_address
        self.endpoint_port = port
        self.tag = tag

        name = config.name
        self.host_name = None
        if not name is None:
            self.host_name = os.path.basename(name)

        # Initialize token value if we're working in Direct mode.
        if not config.datahub:
            self.token = ''
            self.token = self.try_load_token_from_config()
            if (self.token is None) or (self.token == ''):
                self.token = self.try_obtain_token()
            config.system_stats_token_required()

        cert_name = None

        if not config.use_ca_provided:
            cert_name = system_cert_file()
            if cert_name is None:
                cert_name = default_cert_file(config)
        else:
            cert_name = default_cert_file(config)

        if use_ssl and not cert_name:
            die('Cannot get default certificate file name to provide connection over SSL!')

        self.transport = StreamLogSender(self.tag, self.endpoint_address, self.endpoint_port, use_ssl,
                                         cert_name)
        self.stat_sender_thread = StatisticsSendingWorker(self.transport, self.msg_queue)
        self.stat_sender_thread.setDaemon(True)
        self.stat_sender_thread.start()

    @staticmethod
    def try_load_token_from_config():
        return config.system_stats_token

    @staticmethod
    def get_log_token(name, filename, type_opt):
        config.agent_key_required()
        log_request = {"request": "new_log",
                       "user_key": config.user_key,
                       "host_key": config.agent_key,
                       "name": name,
                       "filename": filename,
                       "type": type_opt,
                       "source": "token",
                       "retention": -1}
        log_response = api_request(log_request, True, True)
        token = NOT_SET
        try:
            log_set = log_response['log']
            token = log_set['token']
        except KeyError:
            die("Cannot obtain token for " + filename + " log file. The response is corrupted.")

        return token

    @staticmethod
    def try_obtain_token(name=SYSTEM_STATS_LOG_FILE, filename=SYSTEM_STATS_LOG_FILE, type_opt=''):
        config.system_stats_token = SyslogStreamSender.get_log_token(name, filename, type_opt)
        config.save()
        return config.system_stats_token

    def push(self, msg):
        # Prefix the message with host name
        if not self.host_name is None:
            msg = "HostName=" + self.host_name + " " + msg
        if not config.datahub:
            # Sending directly tod Logentries service - token is required
            self.msg_queue.append(self.token + " " + msg)
        else:
            # Sending to DataHub - append hostname to the message
            self.msg_queue.append(msg)


def debug_filters(msg, *args):
    if config.debug_filters:
        print >> sys.stderr, msg % args

#
# Imports that may not be available
#

try:
    import json

    try:
        json_loads = json.loads
        json_dumps = json.dumps
    except AttributeError:
        json_loads = json.read
        json_dumps = json.write
except ImportError:
    try:
        import simplejson
    except ImportError:
        die('NOTE: Please install Python "simplejson" package (python-simplejson) or a newer Python (2.6).')
    json_loads = simplejson.loads
    json_dumps = simplejson.dumps

no_ssl = False
try:
    import ssl

    wrap_socket = ssl.wrap_socket
    CERT_REQUIRED = ssl.CERT_REQUIRED

except ImportError:
    no_ssl = True

    try:
        _ = httplib.HTTPSConnection
    except AttributeError:
        die('NOTE: Please install Python "ssl" module.')

    def wrap_socket(sock, ca_certs=None, cert_reqs=None):
        return socket.ssl(sock)

    CERT_REQUIRED = 0

#
# Custom proctitle
#


#
# User-defined filtering code
#

def filter_events(events):
    """
    User-defined filtering code. Events passed are about to be sent to
    logentries server. Make the required modifications to the events such
    as removing unwanted or sensitive information.
    """
    # By default, this method is empty
    return events


def default_filter_filenames(filename):
    """
    By default we allow to follow any files specified in the condifuration.
    """
    return True


def call(command):
    """
    Calls the given command in OS environment.
    """
    x = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).stdout.read()
    if len(x) == 0: return ''
    if x[-1] == '\n': x = x[0:len(x) - 1]
    return x


def uniq(arr):
    """
    Returns the list with duplicate elements removed.
    """
    return list(set(arr))


def _lock_pid_file_name():
    """
    Returns path to a file for protecting critical section
    for daemonizing (see daemonize() )
    """
    return config.pid_file + '.lock'


def _lock_pid():
    """
    Tries to exclusively open file for protecting of critical section
    for daemonizing.
    """
    file_name = _lock_pid_file_name()
    try:
        fd = os.open(file_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except OSError:
        return None
    if -1 == fd:
        return None
    os.close(fd)
    return True


def _unlock_pid():
    """
    Releases file for protecting of critical section for daemonizing.
    """
    try:
        file_name = _lock_pid_file_name()
        os.remove(file_name)
    except OSError:
        pass


def _try_daemonize():
    """
    Creates a daemon from the current process.
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    Alternative: python-daemon
    """

    try:
        pidfile = file(config.pid_file, 'r')
        pid = int(pidfile.read().strip())
        pidfile.close()
    except IOError:
        pid = None
    if pid:
        if not os.path.exists('/proc') or os.path.exists("/proc/%d/status" % pid):
            return "Pidfile %s already exist. Daemon already running?" % config.pid_file

    try:
        # Open pid file
        if config.pid_file:
            file(config.pid_file, 'w').close()

        pid = os.fork()
        if pid > 0:
            sys.exit(EXIT_OK)
        os.chdir("/")
        os.setsid()
        os.umask(0)
        pid = os.fork()
        if pid > 0:
            sys.exit(EXIT_OK)
        sys.stdout.flush()
        sys.stderr.flush()
        si = file('/dev/null', 'r')
        so = file('/dev/null', 'a+')
        se = file('/dev/null', 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Write pid file
        if config.pid_file:
            pid = str(os.getpid())
            pidfile = file(config.pid_file, 'w')
            atexit.register(rm_pidfile)
            pidfile.write("%s\n" % pid)
            pidfile.close()
    except OSError, e:
        rm_pidfile(config)
        return "Cannot daemonize: %s" % e.strerror
    return None


def daemonize():
    """
    Creates a daemon from the current process.

    It uses helper file as a lock and then checks inside critical section
    whether pid file contains pid of a valid process.
    If not then it daemonizes itself, otherwise it dies.
    """
    if not _lock_pid():
        die("Daemon already running. If you are sure it isn't please remove %s" % _lock_pid_file_name())
    err = _try_daemonize()
    _unlock_pid()
    if err:
        die("%s" % err)

    # Setting the proctitle
    set_proc_title('logentries-daemon')

    # Logging for daemon mode
    log.removeHandler(stream_handler)
    shandler = logging.StreamHandler()
    shandler.setLevel(logging.DEBUG)
    shandler.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
    log.addHandler(shandler)


def print_total(elems, name):
    """
    Prints total number of elements in the list
    """
    total = len(elems)
    if total == 0:
        report("no %ss" % name)
    elif total == 1:
        report("1 " + name)
    else:
        report("%d %ss" % (total, name))


def collect_log_names(system_info):
    """
    Collects standard local logs and identifies them.
    """
    logs = []
    for root, dirs, files in os.walk(LOG_ROOT):
        for name in files:
            if name[-3:] != '.gz' and re.match(r'.*\.\d+$', name) == None:
                logs.append(os.path.join(root, name))

    log.debug("Collected logs: %s" % logs)
    try:
        c = httplib.HTTPSConnection(LE_SERVER_API)
        request = {
            'logs': json_dumps(logs),
            'distname': system_info['distname'],
            'distver': system_info['distver']
        }
        log.debug("Requesting %s" % request)
        c.request('post', ID_LOGS_API, urllib.urlencode(request), {})
        response = c.getresponse()
        if not response or response.status != 200:
            die('Error: Unexpected response from logentries (%s).' % response.status)
        data = json_loads(response.read())
        log_data = data['logs']

        log.debug("Identified logs: %s" % log_data)
    except socket.error, msg:
        die('Error: Cannot contact server, %s' % msg)
    except ValueError, msg:
        die('Error: Invalid response from the server (Parsing error %s)' % msg)
    except KeyError:
        die('Error: Invalid response from the server, log data not present.')

    return log_data


def lsb_release(system_info):
    # General LSB system
    if os.path.isfile(LSB_RELEASE):
        try:
            fields = dict((a.split('=') for a in rfile(LSB_RELEASE).split('\n') if len(a.split('=')) == 2))
            system_info['distname'] = fields['DISTRIB_ID']
            system_info['distver'] = fields['DISTRIB_RELEASE']
            return True
        except ValueError:
            pass
        except KeyError:
            pass

    # Information not found
    return False


def release_test(filename, distname, system_info):
    if os.path.isfile(filename):
        system_info['distname'] = distname
        system_info['distver'] = rfile(filename)
        return True
    return False


def system_detect(details):
    """
    Detects the current operating system. Returned information contains:
        distname: distribution name
        distver: distribution version
        kernel: kernel type
        system: system name
        hostname: host name
    """
    uname = platform.uname()
    sys = uname[0]
    system_info = dict(system=sys, hostname=socket.getfqdn(),
                       kernel='', distname='', distver='')

    if not details: return system_info

    if sys == "SunOS":
        pass
    elif sys == "AIX":
        system_info['distver'] = call("oslevel -r")
    elif sys == "Darwin":
        system_info['distname'] = call("sw_vers -productName")
        system_info['distver'] = call("sw_vers -productVersion")
        system_info['kernel'] = uname[2]

    elif sys == "Linux":
        system_info['kernel'] = uname[2]
        # XXX CentOS?
        releases = [
            ['/etc/debian_version', 'Debian'],
            ['/etc/UnitedLinux-release', 'United Linux'],
            ['/etc/annvix-release', 'Annvix'],
            ['/etc/arch-release', 'Arch Linux'],
            ['/etc/arklinux-release', 'Arklinux'],
            ['/etc/aurox-release', 'Aurox Linux'],
            ['/etc/blackcat-release', 'BlackCat'],
            ['/etc/cobalt-release', 'Cobalt'],
            ['/etc/conectiva-release', 'Conectiva'],
            ['/etc/fedora-release', 'Fedora Core'],
            ['/etc/gentoo-release', 'Gentoo Linux'],
            ['/etc/immunix-release', 'Immunix'],
            ['/etc/knoppix_version', 'Knoppix'],
            ['/etc/lfs-release', 'Linux-From-Scratch'],
            ['/etc/linuxppc-release', 'Linux-PPC'],
            ['/etc/mandriva-release', 'Mandriva Linux'],
            ['/etc/mandrake-release', 'Mandrake Linux'],
            ['/etc/mandakelinux-release', 'Mandrake Linux'],
            ['/etc/mklinux-release', 'MkLinux'],
            ['/etc/nld-release', 'Novell Linux Desktop'],
            ['/etc/pld-release', 'PLD Linux'],
            ['/etc/redhat-release', 'Red Hat'],
            ['/etc/slackware-version', 'Slackware'],
            ['/etc/e-smith-release', 'SME Server'],
            ['/etc/release', 'Solaris SPARC'],
            ['/etc/sun-release', 'Sun JDS'],
            ['/etc/SuSE-release', 'SuSE'],
            ['/etc/sles-release', 'SuSE Linux ES9'],
            ['/etc/tinysofa-release', 'Tiny Sofa'],
            ['/etc/turbolinux-release', 'TurboLinux'],
            ['/etc/ultrapenguin-release', 'UltraPenguin'],
            ['/etc/va-release', 'VA-Linux/RH-VALE'],
            ['/etc/yellowdog-release', 'Yellow Dog'],
        ]

        # Check for known system IDs
        for release in releases:
            if release_test(release[0], release[1], system_info):
                break
        # Check for general LSB system
        if os.path.isfile(LSB_RELEASE):
            try:
                fields = dict((a.split('=') for a in rfile(LSB_RELEASE).split('\n') if len(a.split('=')) == 2))
                system_info['distname'] = fields['DISTRIB_ID']
                system_info['distver'] = fields['DISTRIB_RELEASE']
            except ValueError:
                pass
            except KeyError:
                pass
    return system_info


# Identified ranges

SEC = 1000
MIN = 60 * SEC
HOUR = 60 * MIN
DAY = 24 * HOUR
MON = 31 * DAY
YEAR = 365 * DAY


def date_patterns():
    """ Generates date patterns of the form [day<->month year?]. """
    for year in [' %Y', ' %y']:
        for mon in ['%b', '%B', '%m']:
            yield ['%%d %s%s' % (mon, year), DAY, []]
            yield ['%s %%d%s' % (mon, year), DAY, []]
    for mon in ['%b', '%B']:  # Year empty
        yield ['%%d %s' % (mon), DAY, [YEAR]]
        yield ['%s %%d' % (mon), DAY, [YEAR]]
    yield ['%%Y %%d %s' % (mon), DAY, []]
    yield ['%%Y %s %%d' % (mon), DAY, []]
    yield ['%Y %m %d', DAY, []]


def time_patterns(c_cols):
    """ Generates time patterns of the form [hour:min:sec?] including empty time. """
    if c_cols >= 2:
        yield ['%H:%M:%S', SEC, []]
    if c_cols >= 1:
        yield ['%H:%M', MIN, []]
        yield ['%I:%M%p', MIN, []]
    yield ['%I%p', HOUR, []]


def datetime_patterns(c_cols):
    """
    Generates combinations of date and time patterns.
    """
    # Generate dates only
    for d in date_patterns():
        yield d

    # Generate combinations
    for t in time_patterns(c_cols):
        for d in date_patterns():
            yield ['%s %s' % (d[0], t[0]), t[1], d[2]]
            yield ['%s %s' % (t[0], d[0]), t[1], d[2]]
        yield [t[0], t[1], [YEAR, MON, DAY]]


def timestamp_patterns(sample):
    """
    Generates all timestamp patterns we can handle. It is constructed by generating all possible combinations
    of date, time, day name and zone. The pattern is [day_name? date<->time zone?] plus simple date and time.
    """
    # All timestamps variations
    day_name = ''
    if len(sample) > 0:
        if sample[0] in string.ascii_letters:
            day_name = '%a '
    c_cols = sample.count(':')
    for zone in ['', ' %Z', ' %z']:
        for dt in datetime_patterns(c_cols):
            yield ['%s%s%s' % (day_name, dt[0], zone), dt[1], dt[2]]


def timestamp_group(text):
    """
    Returns a tuple [timestamp, range] which corresponds to the date and time given. Exists on parse error.
    """
    timep = re.sub(r' +', ' ', re.sub(r'[-,./]', ' ', text)).strip()
    start_tuple = None
    for p in timestamp_patterns(timep):
        pattern, resolution, filling = p
        try:
            start_tuple = time.strptime(timep, p[0])
            break
        except ValueError:
            pass
    if not start_tuple:
        die("Error: Date '%s' not recognized" % text)

    today = datetime.date.today()
    # Complete filling
    if YEAR in filling:
        start_tuple.rm_year = today.year
    if MON in filling:
        start_tuple.rm_month = today.month
    if DAY in filling:
        start_tuple.rm_day = today.day
    return [int(time.mktime(start_tuple)) * 1000, resolution]


def timestamp_range(text):
    """
    Identifies range in the text given. Returns -1 if the range has not been identified.
    """

    # Parse range
    m = re.match(r'^(last)?\s*(\d+)?\s*(s|sec|second|m|min|minute|h|hour|d|day|mon|month|y|year)s?$', text.strip())
    if not m:
        return -1
    count = m.group(2)  # Count of time frames
    tf = m.group(3)  # Time frame
    # Get count
    if count:
        count = int(count)
    else:
        count = 1
    # Get time frame
    f_groups = [
        [['s', 'sec', 'second'], SEC],
        [['m', 'min', 'minute'], MIN],
        [['h', 'hour'], HOUR],
        [['d', 'day'], DAY],
        [['mon', 'month'], MON],
        [['y', 'year'], YEAR],
    ]
    for tg in f_groups:
        if tf in tg[0]:
            return count * tg[1]
    return -1


def parse_timestamp_range(text):
    """
    Parses the time range given and return start-end pair of timestamps.

    Recognized structures are:
    t|today
    y|yesterday
    last? \d* (m|min|minute|h|hour|d|day|mon|month|y|year) s?
    range
    datetime
    datetime -> range
    datetime -> datetime
    """

    text = text.strip()
    # No time frame
    if text == '':
        return [0, 9223372036854775807]

    # Day spec
    now = datetime.datetime.now()
    if text in ['t', 'today']:
        today = int(time.mktime(datetime.datetime(now.year, now.month, now.day).timetuple())) * 1000
        return [today, today + DAY]
    if text in ['y', 'yesterday']:
        yesterday = int(time.mktime(
            (datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days=1)).timetuple())) * 1000
        return [yesterday, yesterday + DAY]

    # Range spec
    parts = text.split('->')
    r = timestamp_range(parts[0])
    if (r != -1 and len(parts) > 1) or len(parts) > 2:
        die("Error: Date and range '%s' has invalid structure" % text)
    if r != -1:
        now = int(time.time() * 1000)
        return [now - r, now]

    # Date spec
    start_group = timestamp_group(parts[0])
    start = start_group[0]
    end = start + start_group[1]

    if len(parts) > 1:
        end_range = timestamp_range(parts[1])
        if end_range != -1:
            end = start + end_range
        else:
            end_group = timestamp_group(parts[1])
            end = end_group[0] + end_group[1]

    return [start, end]


def choose_account_key(accounts):
    """
    Allows user to select the right account.
    """
    if len(accounts) == 0:
        die('No account is associated with your profile. Log in to Logentries to create a new account.')
    if len(accounts) == 1:
        return accounts[0]['account_key']

    for i in range(0, len(accounts)):
        account = accounts[i]
        print >> sys.stderr, '[%s] %s %s' % (i, account['account_key'][:8], account['name'])

    while True:
        try:
            selection = int(raw_input('Pick account you would like to use: '))
            if selection in range(0, len(accounts)):
                return accounts[selection]['account_key']
        except ValueError:
            pass
        print >> sys.stderr, 'Invalid choice. Please try again or break with Ctrl+C.'


def retrieve_account_key():
    """
    Retrieves account keys from the web server.
    """
    while True:
        username = raw_input('Email: ')
        password = getpass.getpass()

        try:
            c = domain_connect(config, Domain.MAIN, Domain)
            c.request('POST', ACCOUNT_KEYS_API,
                      urllib.urlencode({'username': username, 'password': password}),
                      {
                          'Referer': 'https://logentries.com/login/',
                          'Content-type': 'application/x-www-form-urlencoded',
                      })
            response = c.getresponse()
            if not response or response.status != 200:
                resp_val = 'err'
                if response:
                    resp_val = response.status
                if resp_val == 403:
                    print >> sys.stderr, 'Error: Login failed. Invalid credentials.'
                else:
                    print >> sys.stderr, 'Error: Unexpected login response from logentries (%s).' % resp_val
            else:
                data = json_loads(response.read())
                return choose_account_key(data['accounts'])
        except socket.error, msg:
            print >> sys.stderr, 'Error: Cannot contact server, %s' % msg
        except ValueError, msg:
            print >> sys.stderr, 'Error: Invalid response from the server (Parsing error %s)' % msg
        except KeyError:
            print >> sys.stderr, 'Error: Invalid response from the server, user key not present.'

        print >> sys.stderr, 'Try to log in again, or press Ctrl+C to break'


class Stats:
    """
    Collects statistics about the system work load.
    """

    def __init__(self):
        self.timer = None
        self.to_remove = False
        self.first = True

        # Memory fields we are looking for in /proc/meminfo
        self.MEM_FIELDS = ['MemTotal:', 'Active:', 'Cached:']
        # Block devices in the system
        all_devices = [os.path.basename(filename) for filename in glob.glob(SYS_BLOCK_DEV + '/*')]
        # Monitored devices (all devices except loop)
        self.our_devices = frozenset([device_name for device_name in all_devices if
                                      not device_name.startswith("loop") and not device_name.startswith(
                                          "ram") and not device_name.startswith("md")])

        self.prev_cpu_stats = [0, 0, 0, 0, 0, 0, 0]
        self.prev_disk_stats = [0, 0]
        self.prev_net_stats = [0, 0]
        self.total = {}
        self.total['dr'] = 0
        self.total['dw'] = 0
        self.total['ni'] = 0
        self.total['no'] = 0

        self.procfilesystem = True
        if not os.path.exists(CPUSTATS_FILE):
            # store system type for later reference in pulling stats
            # in an alternate manner
            self.procfilesystem = False
            self.uname = platform.uname()
            self.sys = self.uname[0]
            log.debug('sys: %s' % (self.sys))

        # for scaling in osx_top_stats -- key is a scale factor (gig,
        # meg, etc), value is what to multiply by to get to kilobytes
        self.scale2kb = {'M': 1024, 'G': 1048576}

        if not config.debug_nostats:
            PORT = {False: LE_DEFAULT_SSL_PORT, True: LE_DEFAULT_NON_SSL_PORT}
            hostname = Domain.STREAM
            port = PORT[config.suppress_ssl]
            if config.datahub:
                hostname = config.datahub_ip
                port = config.datahub_port

            self.stats_stream = SyslogStreamSender(SYSTEM_STATS_TAG, hostname, port,
                                                   not config.suppress_ssl)
            self.send_stats()


    @staticmethod
    def save_data(data, name, value):
        """
        Saves the value under the name given. Negative values are set to 0.
        """
        if value >= 0:
            data[name] = value
        else:
            data[name] = 0

    def cpu_stats(self, data):
        """
        Collects CPU statistics. Virtual ticks are ignored.
        """
        try:
            for line in fileinput.input([CPUSTATS_FILE]):
                if len(line) < 13:
                    continue
                if line.startswith('cpu '):
                    raw_stats = [long(part) for part in line.split()[1:8]]
                    break
            fileinput.close()
        except IOError:
            return

        self.save_data(data, 'cu', raw_stats[0] - self.prev_cpu_stats[0])
        self.save_data(data, 'cl', raw_stats[1] - self.prev_cpu_stats[1])
        self.save_data(data, 'cs', raw_stats[2] - self.prev_cpu_stats[2])
        self.save_data(data, 'ci', raw_stats[3] - self.prev_cpu_stats[3])
        self.save_data(data, 'cio', raw_stats[4] - self.prev_cpu_stats[4])
        self.save_data(data, 'cq', raw_stats[5] - self.prev_cpu_stats[5])
        self.save_data(data, 'csq', raw_stats[6] - self.prev_cpu_stats[6])
        self.prev_cpu_stats = raw_stats

    def disk_stats(self, data):
        """
        Collects disk statistics. Interested in block devices only.
        """
        reads = 0L
        writes = 0L
        # For all block devices
        for device in self.our_devices:
            try:
                # Read device stats
                f = open(SYS_BLOCK_DEV + device + '/stat', 'r')
                line = f.read()
                f.close()
            except IOError:
                continue

            # Parse device stats
            parts = line.split()
            if len(parts) < 7:
                continue
            reads += long(parts[2])
            writes += long(parts[6])

        reads *= 512
        writes *= 512
        self.save_data(data, 'dr', reads - self.prev_disk_stats[0])
        self.save_data(data, 'dw', writes - self.prev_disk_stats[1])
        self.prev_disk_stats = [reads, writes]
        self.total['dr'] = reads
        self.total['dw'] = writes

    def mem_stats(self, data):
        """
        Collects memory statistics.
        """
        mem_vars = {}
        for field in self.MEM_FIELDS:
            mem_vars[field] = 0L
        try:
            for line in fileinput.input([MEMSTATS_FILE]):
                parts = line.split()
                name = parts[0]
                if name in self.MEM_FIELDS:
                    mem_vars[name] = long(parts[1])
            fileinput.close()
        except IOError:
            return
        self.save_data(data, 'mt', mem_vars[self.MEM_FIELDS[0]])
        self.save_data(data, 'ma', mem_vars[self.MEM_FIELDS[1]])
        self.save_data(data, 'mc', mem_vars[self.MEM_FIELDS[2]])

    def net_stats(self, data):
        """
        Collects network statistics. Collecting only selected interfaces.
        """
        receive = 0L
        transmit = 0L
        try:
            for line in fileinput.input([NETSTATS_FILE]):
                if line[:5] in NET_DEVICES:
                    parts = line.replace(':', ' ').split()
                    receive += long(parts[1])
                    transmit += long(parts[9])
            fileinput.close()
        except IOError:
            return

        self.save_data(data, 'ni', receive - self.prev_net_stats[0])
        self.save_data(data, 'no', transmit - self.prev_net_stats[1])
        self.prev_net_stats = [receive, transmit]
        self.total['ni'] = receive
        self.total['no'] = transmit

    def osx_top_stats(self, data):
        """
        Darwin/OS-X doesn't seem to provide nearly the same amount of
        detail as the /proc filesystem under Linux -- at least not
        easily accessible to the command line.  The headers from
        top(1) seem to be the quickest & most detailed source of data
        about CPU, and disk transfer as separated into reads & writes.
        (vs. iostat, which shows CPU less granularly; it shows more
         detail about per-disk IO, but does not split IO into reads and
         writes)

        Frustratingly, the level of per-disk statistics from top is
        incredibly un-granular

        We'll get physical memory details from here too
        """
        cpure = re.compile('CPU usage:\s+([\d.]+)\% user, ([\d.]+)\% sys, '
                           '([\d.]+)\% idle')
        memre = re.compile('PhysMem:\s+(\d+\w+) wired, '
                           '(\d+\w+) active, (\d+\w+) inactive, '
                           '(\d+\w+) used, (\d+\w+) free.')
        diskre = re.compile('Disks: (\d+)/(\d+\w+) read, '
                            '(\d+)/(\d+\w+) written.')

        # scaling routine for use in map() later
        def scaletokb(value):
            # take a value like 1209M or 10G and return an integer
            # representing the value in kilobytes

            (size, scale) = re.split('([A-z]+)', value)[:2]
            size = int(size)
            if scale:
                if self.scale2kb.has_key(scale):
                    size *= self.scale2kb[scale]
                else:
                    log.warning("Error: value in %s expressed in "
                                "dimension I can't translate to kb: %s %s" %
                                (line, size, scale))
            return size

        # the first set of 'top' headers display average values over
        # system uptime.  so we only want to read the second set that we
        # see.
        toppass = 0

        # we should really do this first, so that we don't waste any time
        # if top fails to work.  however, it 'reads' better at this point
        try:
            proc = subprocess.Popen(['top',
                                     '-i', '2', '-l', '2', '-n', '0'],
                                    stdout=subprocess.PIPE)
        except:
            return

        for line in proc.stdout:
            # skip the first output
            if line.startswith('Processes: '):
                toppass += 1
            elif line.startswith('CPU usage: ') and toppass == 2:
                cpuresult = cpure.match(line)
                """
                the data we send to logentries is expected to be in terms
                of centiseconds of (user/system/idle/etc) time as all we
                have is %, multiply that % by the EPOCH and 100.
                """
                if cpuresult:
                    (cu, cs, ci) = map(lambda x: int(float(x) * 100 * EPOCH),
                                       cpuresult.group(1, 2, 3))
                    self.save_data(data, 'cu', cu)
                    self.save_data(data, 'cs', cs)
                    self.save_data(data, 'ci', ci)
                    # send zero in case all must be present
                    self.save_data(data, 'cl', 0)
                    self.save_data(data, 'cio', 0)
                    self.save_data(data, 'cq', 0)
                    self.save_data(data, 'csq', 0)
                else:
                    log.warning("Error: could not parse CPU stats "
                                "in top output line %s" % (line))

            elif line.startswith('PhysMem: ') and toppass == 2:
                """
                OS-X has no fixed cache size -- cached pages are stored in
                virtual memory as part of the Unified Buffer Cache.  It
                would appear to be nearly impossible to find out what the
                current size of the UBC is, save running purge(8) and
                comparing the values before and after -- UBC uncertainty
                principal? :-)

                http://wagerlabs.com/blog/2008/03/04/hacking-the-mac-osx-unified-buffer-cache/
                books.google.ie/books?isbn=0132702266
                http://reviews.cnet.com/8301-13727_7-57372267-263/purge-the-os-x-disk-cache-to-analyze-memory-usage/
                """
                memresult = memre.match(line)
                if memresult:
                    # logentries is expecting values in kilobytes
                    (wired, active, inactive, used, free) = map(
                        scaletokb, memresult.group(1, 2, 3, 4, 5))
                    self.save_data(data, 'mt', used + free)
                    self.save_data(data, 'ma', active)
                    self.save_data(data, 'mc', 0)
                else:
                    log.warning("Error: could not parse memory stats "
                                "in top output line %s" % (line))

            elif line.startswith('Disks: ') and toppass == 2:
                diskresult = diskre.match(line)
                """
                the data we send to logentries is expected to be in bytes
                """
                if diskresult:
                    (reads, writes) = map(scaletokb,
                                          diskresult.group(2, 4))
                    reads *= 1024
                    writes *= 1024

                    self.save_data(data, 'dr',
                                   reads - self.prev_disk_stats[0])
                    self.save_data(data, 'dw',
                                   writes - self.prev_disk_stats[1])
                    self.prev_disk_stats = [reads, writes]
                else:
                    log.warning("Error: could not parse disk stats "
                                "in top output line %s" % (line))

    def netstats_stats(self, data):
        """
        Read network bytes in/out from the output of "netstat -s"
        Not exact, as on OS-X it doesn't display bytes for every protocol,
        but more exact than using 'top' or 'netstat <interval>'
        """
        try:
            proc = subprocess.Popen(['netstat', '-bi'],
                                    stdout=subprocess.PIPE)
        except:
            return

        # if we see 11 non-blank fields,
        # #7 is input bytes, and #10 is output bytes, but avoid duplicate
        # device lines

        receive = 0L
        transmit = 0L
        netseen = {}

        for line in proc.stdout:
            if line.startswith('Name'):
                continue

            parts = line.split()
            if len(parts) != 11:
                continue
            if netseen.has_key(parts[1]):
                continue
            if not parts[6].isdigit():
                continue

            receive += long(parts[6])
            transmit += long(parts[9])
            netseen[parts[0]] = 1

        self.save_data(data, 'ni', receive - self.prev_net_stats[0])
        self.save_data(data, 'no', transmit - self.prev_net_stats[1])
        self.prev_net_stats = [receive, transmit]

    def stats(self):
        """Collects statistics."""
        data = {}

        if self.procfilesystem:
            self.cpu_stats(data)
            self.disk_stats(data)
            self.mem_stats(data)
            self.net_stats(data)
        else:
            if self.sys == "Darwin":
                self.osx_top_stats(data)
                self.netstats_stats(data)
        return data

    @staticmethod
    def new_request(rq):
        try:
            response = api_request(rq, silent=not config.debug, die_on_error=False)
            if config.debug_stats:
                log.info(response)
        except socket.error, (err_no, err_str):
            pass

    def send_stats(self):
        """
        Collects all statistics and sends them to Logentries.
        """
        ethalon = time.time()

        results = self.stats()
        results['request'] = RQ_WORKLOAD
        results['host_key'] = config.agent_key
        if config.debug_stats:
            log.info(results)
        if not self.first:
            # Send data
            if not config.datahub:
                self.new_request(results)
            self.stats_stream.push(self.stats_to_string(results))
        else:
            self.first = False

        ethalon += EPOCH
        next_step = (ethalon - time.time()) % EPOCH
        if not self.to_remove:
            self.timer = threading.Timer(next_step, self.send_stats, ())
            self.timer.daemon = True
            self.timer.start()

    def stats_to_string(self, data):
        total = data['cu'] + data['cl'] + data['cs'] + data['ci'] + data['cio'] + data['cq'] + data['csq']
        cu = data['cu'] * 100 / total
        cl = data['cl'] * 100 / total
        cs = data['cs'] * 100 / total
        ci = data['ci'] * 100 / total
        cio = data['cio'] * 100 / total
        cq = data['cq'] * 100 / total
        csq = data['csq'] * 100 / total
        stat_cpu_string = "CPU.user={0}% CPU.nice={1}% CPU.system={2}% CPU.idle={3}% CPU.wait={4}% CPU.irq={5}% CPU.softirq={6}% ".format(
            cu, cl, cs, ci, cio, cq, csq)
        stat_mem_string = "Mem.total={0} Mem.active={1} Mem.cached={2} ".format(data['mt'], data['ma'], data['mc'])
        stat_disk_string = "Disk.write={0} Disk.read={1} ".format(self.total['dw'], self.total['dr'])
        stat_net_string = "Net.send={0} Net.resv={1} ".format(self.total['no'], self.total['ni'])
        host_string = "HostName={0} ".format(config.hostname_required())
        return host_string + stat_cpu_string + stat_mem_string + stat_disk_string + stat_net_string

    def cancel(self):
        self.to_remove = True
        if self.timer:
            self.timer.cancel()


class Follower(object):
    """
    The follower keeps an eye on the file specified and sends new events to the logentries infrastructure.
    """

    def __init__(self, name, log_key, monitorlogs, event_filter):
        """ Initializes the follower. """
        self.name = name
        self.log_key = log_key
        self.log_addr = '/%s/hosts/%s/%s/?realtime=1' % (config.user_key, config.agent_key, log_key)
        self.flush = True
        self.event_filter = event_filter

        if not config.datahub:
            self.syslog_sender = SyslogStreamSender(os.path.basename(name), Domain.STREAM, config.get_port(),
                                                    not config.suppress_ssl)
        else:
            self.syslog_sender = SyslogStreamSender(os.path.basename(name), config.datahub_ip, config.datahub_port,
                                                    not config.suppress_ssl)
        log.info("Following %s" % name)
        monitoring_thread = threading.Thread(target=monitorlogs, name=self.name)
        monitoring_thread.daemon = True
        monitoring_thread.start()

    def file_candidate(self):
        """
        Returns list of file names which corresponds to the specified template.
        """
        try:
            candidates = glob.glob(self.name)

            if len(candidates) == 0:
                return None

            candidate_times = [[os.path.getmtime(name), name] for name in candidates]
            candidate_times.sort()
            candidate_times.reverse()
            return candidate_times[0][1]
        except os.error:
            return None

    def open_log(self):
        """
        Keeps trying to re-open the log file. Returns when the file has been opened or when requested to remove.
        """
        error_info = True
        self.real_name = None

        while not shutdown:
            candidate = self.file_candidate()

            if candidate:
                self.real_name = candidate
                try:
                    self.file = None
                    self.file = open(self.real_name)
                    break
                except IOError:
                    pass

            if error_info:
                log.info("Cannot open file '%s', re-trying in %ss intervals" % (self.name, REOPEN_INT))
                error_info = False
            time.sleep(REOPEN_TRY_INTERVAL)

    def log_rename(self):
        """Detects file rename."""

        # Get file candidates
        candidate = self.file_candidate()
        if not candidate: return False

        try:
            ctime1 = os.fstat(self.file.fileno()).st_mtime
            ctime_new = os.path.getmtime(candidate)
            ctime2 = os.fstat(self.file.fileno()).st_mtime
        except os.error:
            pass

        if ctime1 == ctime2 and ctime1 != ctime_new:
            # We have a name change according to the time
            return True

        return False

    def read_log_line(self):
        """ Reads a line from the log. Checks maximal line size. """
        buff = self.file.read(MAX_EVENTS)
        return buff

    def set_file_position(self, offset, start=FILE_BEGIN):
        """ Move the position of filepointers."""
        self.file.seek(offset, start)

    def get_file_position(self):
        """ Returns the position filepointers."""
        pos = self.file.tell()
        return pos

    def get_events(self):
        """
        Returns a block of newly detected events from the log. Returns None in case of timeout.
        """

        # Moves at the end of the log file
        if self.flush:
            self.set_file_position(0, FILE_END)
            self.flush = False

        # TODO: investigate select-like approach?
        idle_cnt = 0
        iaa_cnt = 0
        events = ''
        while iaa_cnt != IAA_INTERVAL and not shutdown:
            # Collect lines
            events = self.read_log_line()
            # ####  print type(events) ##DEBUG
            if len(events) != 0:
                break

            # No more events, wait
            time.sleep(TAIL_RECHECK)

            # Log rename check
            idle_cnt += 1
            if idle_cnt == NAME_CHECK:
                if self.log_rename():
                    self.open_log()
                    iaa_cnt = 0
                else:
                    # Recover from external file modification
                    position = self.get_file_position()
                    self.set_file_position(0, FILE_END)
                    file_size = self.get_file_position()
                    if file_size < position:
                        # File has been externaly modified
                        position = file_size
                    self.set_file_position(position)
                idle_cnt = 0
            else:
                # To reset end-of-line error
                self.set_file_position(self.get_file_position())
            iaa_cnt += 1

        # Send IAA packet if required
        if iaa_cnt == IAA_INTERVAL:
            return None

        return events

    def open_connection(self):
        if config.datahub:
            return
        """ Opens a push connection to logentries. """
        log.debug("Opening connection %s", self.log_addr)
        retry = 1
        while True:
            if retry % 3 == 0:
                self.flush = True
                time.sleep(SRV_RECON_TIMEOUT)
            retry += 1
            try:
                self.conn = data_connect(config, Domain)
                do_request(self.conn, "PUT", self.log_addr)
                break
            except socket.error:
                if shutdown: return

    def send_events(self, events):
        """ Sends a block of new lines. """
        if events:
            events = self.event_filter(events)
            if not events:
                return
        else:
            if config.datahub:
                return
            else:
                events = IAA_TOKEN
        if config.datahub:
            eventsArray = events.splitlines()
            for event in eventsArray:
                self.syslog_sender.push(event)
        else:
            while not shutdown:
                try:
                    self.conn.send(events)
                    break
                except socket.error, (err_no, err_str):
                    self.open_connection()

        if config.debug_events:
            print >> sys.stderr, events,


class LogFollower(Follower):
    def __init__(self, name, log_key, event_filter):
        super(LogFollower, self).__init__(name, log_key, self.monitorlogs, event_filter)

    def monitorlogs(self):
        """ Opens the log file and starts to collect new events. """
        self.open_connection()
        self.open_log()
        while not shutdown:
            try:
                events = self.get_events()
            except IOError, e:
                if config.debug:
                    log.debug("IOError: %s", e)
                self.open_log()
            self.send_events(events)


class Config:
    def __init__(self):
        self.config_dir_name = self.get_config_dir()
        self.config_filename = self.config_dir_name + LE_CONFIG

        # Configuration variables
        self.user_key = DEFAULT_USER_KEY
        self.agent_key = NOT_SET
        self.filters = NOT_SET
        self.name = NOT_SET
        self.hostname = NOT_SET
        self.no_timestamps = False
        self.std = False
        self.std_all = False
        self.type_opt = NOT_SET
        self.xlist = False
        self.uuid = False
        self.daemon = False
        self.winservice = False
        self.pid_file = PID_FILE
        self.system_stats_token = NOT_SET

        # Special options
        self.yes = False
        self.force = False
        self.suppress_ssl = False
        self.use_ca_provided = False

        self.datahub = NOT_SET
        self.datahub_ip = NOT_SET
        self.datahub_port = NOT_SET

        # System stats. token
        self.system_stats_token = NOT_SET

        # Debug options

        # Enabled fine-grained logging
        self.debug = False
        # All recognized events are logged
        self.debug_events = False
        # All filtering actions are logged
        self.debug_filters = False
        # Adapter connects to locahost
        self.debug_local = False
        # Do not collect statistics
        self.debug_nostats = False
        # Collected statistics are logged
        self.debug_stats = False
        # Collect statistics only
        self.debug_stats_only = False
        # Commands passed to server are logged
        self.debug_requests = False
        # Display system information and exit
        self.debug_system = False
        # Display list of logs in the system
        self.debug_loglist = False
        # Force host for api
        self.force_api_host = NOT_SET
        # Force host for data
        self.force_data_host = NOT_SET
        # Force host for this domain
        self.force_domain = NOT_SET

    def get_config_dir(self):
        """
        Identifies a configuration directory for the current user.
        Always terminated with slash.
        """
        if os.geteuid() == 0:
            # Running as root
            c_dir = CONFIG_DIR_SYSTEM
        else:
            # Running as an ordinary user
            c_dir = os.path.expanduser('~') + '/' + CONFIG_DIR_USER

        return c_dir + '/'

    def clean(self):
        """
        Wipes out old configuration file. Returns True if successful.
        """
        try:
            os.remove(self.config_filename)
        except OSError, e:
            if e.errno != 2:
                log.warning("Error: %s: %s" % (self.config_filename, e.strerror))
                return False
        return True


    def basic_setup(self):
        pass

    def load(self):
        """
        Initializes configuration parameters from the configuration
        file.  Returns True if successful, False otherwise. Does not
        touch already defined parameters.
        """

        try:
            conf = ConfigParser.SafeConfigParser({
                USER_KEY_PARAM: '',
                AGENT_KEY_PARAM: '',
                FILTERS_PARAM: '',
                SUPPRESS_SSL_PARAM: '',
                FORCE_DOMAIN_PARAM: '',
                USE_CA_PROVIDED_PARAM: '',
                DATAHUB_PARAM: '',
                SYSSTAT_TOKEN_PARAM: ''
            })
            conf.read(self.config_filename)

            # Load parameters
            if self.user_key == NOT_SET:
                new_user_key = conf.get(MAIN_SECT, USER_KEY_PARAM)
                if new_user_key != '':
                    self.user_key = new_user_key
            if self.agent_key == NOT_SET:
                new_agent_key = conf.get(MAIN_SECT, AGENT_KEY_PARAM)
                if new_agent_key != '':
                    self.agent_key = new_agent_key
            if self.filters == NOT_SET:
                new_filters = conf.get(MAIN_SECT, FILTERS_PARAM)
                if new_filters != '':
                    self.filters = new_filters
            new_suppress_ssl = conf.get(MAIN_SECT, SUPPRESS_SSL_PARAM)
            if new_suppress_ssl == 'True':
                self.suppress_ssl = new_suppress_ssl == 'True'
            new_use_ca_provided = conf.get(MAIN_SECT, USE_CA_PROVIDED_PARAM)
            if new_use_ca_provided == 'True':
                self.use_ca_provided = new_use_ca_provided
            new_force_domain = conf.get(MAIN_SECT, FORCE_DOMAIN_PARAM)
            if new_force_domain:
                self.force_domain = new_force_domain
            if self.datahub == NOT_SET:
                self.set_datahub_settings(conf.get(MAIN_SECT, DATAHUB_PARAM), should_die=False)
            if self.system_stats_token == NOT_SET:
                system_stats_token_str = conf.get(MAIN_SECT, SYSSTAT_TOKEN_PARAM)
                if system_stats_token_str != '':
                    self.system_stats_token = system_stats_token_str

        except ConfigParser.NoSectionError:
            return False
        except ConfigParser.NoOptionError:
            return False
        return True

    def save(self):
        """
        Saves configuration parameters into the configuration file.
        The certification file added as well.
        """
        try:
            conf = ConfigParser.SafeConfigParser()
            create_conf_dir(self)
            conf_file = open(self.config_filename, 'wb')
            conf.add_section(MAIN_SECT)
            if self.user_key != NOT_SET:
                conf.set(MAIN_SECT, USER_KEY_PARAM, self.user_key)
            if self.agent_key != NOT_SET:
                conf.set(MAIN_SECT, AGENT_KEY_PARAM, self.agent_key)
            if self.filters != NOT_SET:
                conf.set(MAIN_SECT, FILTERS_PARAM, self.filters)
            if self.suppress_ssl:
                conf.set(MAIN_SECT, SUPPRESS_SSL_PARAM, 'True')
            if self.use_ca_provided:
                conf.set(MAIN_SECT, USE_CA_PROVIDED_PARAM, 'True')
            if self.force_domain:
                conf.set(MAIN_SECT, FORCE_DOMAIN_PARAM, self.force_domain)
            if self.datahub != NOT_SET:
                conf.set(MAIN_SECT, DATAHUB_PARAM, self.datahub)
            if self.system_stats_token != NOT_SET:
                conf.set(MAIN_SECT, SYSSTAT_TOKEN_PARAM, self.system_stats_token)
            conf.write(conf_file)
        except IOError, e:
            die("Error: IO error when writing to config file: %s" % e)

    def check_key(self, key):
        """
        Checks if the key looks fine
        """
        return len(key) == KEY_LEN

    def set_user_key(self, value):
        if not self.check_key(value):
            die('Error: User key does not look right.')
        self.user_key = value

    def user_key_required(self):
        """
        Exits with error message if the user key is not defined.
        """
        if self.user_key == NOT_SET:
            log.info(
                "Account key is required. Enter your Logentries login credentials or specify the account key with --account-key parameter.")
            self.user_key = retrieve_account_key()
            config.save()

    def set_system_stat_token(self, value):
        if not self.check_key(value):
            die('Error: system stat token does not look right.')
        self.system_stats_token = value

    def system_stats_token_required(self):
        if self.system_stats_token == NOT_SET:
            die("System stat token is required.")
        config.save()

    def set_agent_key(self, value):
        if not self.check_key(value):
            die('Error: Agent key does not look right.')
        self.agent_key = value

    def agent_key_required(self):
        """
        Exits with error message if the agent key is not defined.
        """
        if self.agent_key == NOT_SET:
            die("Agent key is required. Register the host or specify an agent key with the --host-key parameter.")

    def have_agent_key(self):
        """Tests if the agent key has been assigned to this instance."""
        return self.agent_key != ''

    def hostname_required(self):
        """
        Sets the hostname parameter based on server network name. If
        the hostname is set already, it is kept untouched.
        """
        if self.hostname == NOT_SET:
            self.hostname = socket.getfqdn()
        return self.hostname

    def name_required(self):
        """
        Sets host name if not set already. The new host name is
        delivered from its hostname. As a side effect this
        function sets a hostname as well.
        """
        if self.name == NOT_SET:
            self.name = self.hostname_required().split('.')[0]
        return self.name

    # The method gets all parameters of given type from argument list,
    # checks for their format and returns list of values of parameters
    # of specified type. E.g: We have params = ['true', 127.0.0.1, 10000] the call of
    # check_and_get_param_by_type(params, type='bool') yields [True]

    @staticmethod
    def check_and_get_param_by_type(params, type='bool'):
        ret_param = []

        for p in params:
            found = False
            p = p.lower()
            if type == 'ipaddr':
                if p.find('.') != -1:
                    octets = p.split('.', 4)
                    octets_ok = True
                    if len(octets) == 4:
                        for octet in octets:
                            octets_ok &= (octet.isdigit()) and (0 <= int(octet) <= 255)
                    else:
                        octets_ok = False
                    found = octets_ok
            elif type == 'bool':
                if (p.find('true') != -1 and len(p) == 4) or (p.find('false') != -1 and len(p) == 5):
                    found = True
            elif type == 'numeric':
                if p.isdigit():
                    found = True
            else:
                raise NameError('Unknown type name')

            if found:
                if type == 'numeric':
                    ret_param.append(int(p))
                elif type == 'bool':
                    ret_param.append(p == 'true')
                else:
                    ret_param.append(p)

        return ret_param

    def set_datahub_settings(self, value, should_die=True):
        if not value and should_die:
            die('--datahub requires a parameter')
        elif not value and not should_die:
            return

        values = value.split(":")
        if len(values) > 2:
            die("Cannot parse %s for --datahub. Expected format: hostname:port" % value)

        self.datahub_ip = values[0]
        if len(values) == 2:
            try:
                self.datahub_port = int(values[1])
            except ValueError:
                die("Cannot parse %s as port. Specify a valid --datahub address" % values[1])
        self.datahub = value


    def process_params(self, params):
        """
        Parses command line parameters and updates config parameters accordingly
        """
        try:
            optlist, args = getopt.gnu_getopt(params, '',
                                              "user-key= account-key= agent-key= host-key= no-timestamps debug-events "
                                              "debug-filters debug-loglist local debug-stats debug-nostats "
                                              "debug-stats-only debug-cmds debug-system help version yes force uuid list "
                                              "std std-all name= hostname= type= pid-file= debug no-defaults "
                                              "suppress-ssl use-ca-provided force-api-host= force-domain= "
                                              "system-stat-token= datahub=".split())
        except getopt.GetoptError, err:
            die("Parameter error: " + str(err))
        for name, value in optlist:
            if name == "--help":
                print_usage()
            if name == "--version":
                print_usage(True)
            if name == "--yes":
                self.yes = True
            elif name == "--user-key":
                self.set_user_key(value)
            elif name == "--account-key":
                self.set_user_key(value)
            elif name == "--agent-key":
                self.set_agent_key(value)
            elif name == "--host-key":
                self.set_agent_key(value)
            elif name == "--force":
                self.force = True
            elif name == "--list":
                self.xlist = True
            elif name == "--uuid":
                self.uuid = True
            elif name == "--name":
                self.name = value
            elif name == "--hostname":
                self.hostname = value
            elif name == "--pid-file":
                if value == '':
                    self.pid_file = None
                else:
                    self.pid_file = value
            elif name == "--std":
                self.std = True
            elif name == "--type":
                self.type_opt = value
            elif name == "--std-all":
                self.std_all = True
            elif name == "--no-timestamps":
                self.no_timestamps = True
            elif name == "--debug":
                self.debug = True
            elif name == "--debug-events":
                self.debug_events = True
            elif name == "--debug-filters":
                self.debug_filters = True
            elif name == "--local":
                self.debug_local = True
            elif name == "--debug-stats":
                self.debug_stats = True
            elif name == "--debug-nostats":
                self.debug_nostats = True
            elif name == "--debug-stats-only":
                self.debug_stats_only = True
            elif name == "--debug-loglist":
                self.debug_loglist = True
            elif name == "--debug-requests":
                self.debug_requests = True
            elif name == "--debug-system":
                self.debug_system = True
            elif name == "--suppress-ssl":
                self.suppress_ssl = True
            elif name == "--force-api-host":
                if value and value != '': self.force_api_host = value
            elif name == "--force-data-host":
                if value and value != '': self.force_data_host = value
            elif name == "--force-domain":
                if value and value != '': self.force_domain = value
            elif name == "--use-ca-provided":
                self.use_ca_provided = True
            elif name == "--system-stat-token":
                self.set_system_stat_token(value)
            elif name == "--datahub":
                self.set_datahub_settings(value)

        if self.datahub_ip and not self.datahub_port:
            if self.suppress_ssl:
                self.datahub_port = LE_DEFAULT_NON_SSL_PORT
            else:
                self.datahub_port = LE_DEFAULT_SSL_PORT

        if self.debug_local and self.force_api_host:
            die("Do not specify --local and --force-api-host at the same time.")
        if self.debug_local and self.force_data_host:
            die("Do not specify --local and --force-data-host at the same time.")
        if self.debug_local and self.force_domain: die("Do not specify --local and --force-domain at the same time.")
        return args

    def get_port(self):
        PORT = {False: LE_DEFAULT_SSL_PORT, True: LE_DEFAULT_NON_SSL_PORT}
        port = PORT[config.suppress_ssl]
        if self.datahub:
            return config.datahub_port
        return port


config = Config()

# Pass the exception

def do_request(conn, operation, addr, data=None, headers={}):
    log.debug('Domain request: %s %s %s %s' % (operation, addr, data, headers))
    if data:
        conn.request(operation, addr, data, headers=headers)
    else:
        conn.request(operation, addr, headers=headers)


def get_response(operation, addr, data=None, headers={}, silent=False, die_on_error=True, domain=Domain.API):
    """
    Returns response from the domain or API server.
    """
    response = None
    conn = None
    try:
        conn = domain_connect(config, domain, Domain)
        do_request(conn, operation, addr, data, headers)
        response = conn.getresponse()
        return response, conn
    except socket.sslerror, msg:  # Network error
        if not silent:
            log.info("SSL error: %s" % msg)
    except socket.error, msg:  # Network error
        if not silent:
            log.debug("Network error: %s" % msg)
    except httplib.BadStatusLine:
        error = "Internal error, bad status line"
        if die_on_error:
            die(error)
        else:
            log.info(error)

    return None, None


def api_request(request, required=False, check_status=False, silent=False, die_on_error=True):
    """
    Processes a request on the logentries domain.
    """
    # Obtain response
    response, conn = get_response("POST", LE_SERVER_API, urllib.urlencode(request),
                                  silent=silent, die_on_error=die_on_error, domain=Domain.API)

    # Check the response
    if not response:
        if required:
            die("Error: Cannot process LE request, no response")
        if conn:
            conn.close()
        return None
    if response.status != 200:
        if required:
            die("Error: Cannot process LE request: (%s)" % response.status)
        conn.close()
        return None

    xresponse = response.read()
    conn.close()
    log.debug('Domain response: "%s"' % xresponse)
    try:
        d_response = json_loads(xresponse)
    except ValueError:
        error = 'Error: Invalid response, parse error.'
        if die_on_error:
            die(error)
        else:
            log.info(error)
            d_response = None

    if check_status and d_response['response'] != 'ok':
        error = "Error: %s" % d_response['reason']
        if die_on_error:
            die(error)
        else:
            log.info(error)
            d_response = None

    return d_response


def pull_request(what, params):
    """
    Processes a pull request on the logentries domain.
    """
    response = None

    # Obtain response
    addr = '/%s/%s/?%s' % (config.user_key, urllib.quote(what), urllib.urlencode(params))
    response, conn = get_response("GET", addr, domain=Domain.PULL)

    # Check the response
    if not response:
        die("Error: Cannot process LE request, no response")
    if response.status == 404:
        die("Error: Log not found")
    if response.status != 200:
        die("Error: Cannot process LE request: (%s)" % response.status)

    while True:
        data = response.read(65536)
        if len(data) == 0: break
        sys.stdout.write(data)
    conn.close()


def push_request(ilog, data_size, where, params):
    """
    Processes a push request to the logentries domain.
    """
    # Obtain response
    addr = '/%s/%s/?%s' % (config.user_key, urllib.quote(where), urllib.urlencode(params))
    try:
        conn = data_connect(config, Domain)
        do_request(conn, "PUT", addr, headers={CONTENT_LENGTH: '%s' % data_size})

        # Push the file
        to_send = data_size
        while to_send != 0:
            to_read = to_send
            if to_read > 65536:
                to_read = 65536
            data = ilog.read(to_read)
            if len(data) == 0: break
            to_send -= len(data)
            conn.send(data)
        response = conn.getresponse()
        if response.status != 200:
            reason = response.read()
            try:
                d_response = json_loads(reason)
                reason = d_response['reason']
            except ValueError:
                pass
            die('Error: ' + reason)
        conn.close()
    except socket.sslerror, msg:  # Network error
        log.info("SSL error: %s" % msg)
    except socket.error, msg:  # Network error
        log.info("Network error: %s" % msg)

        # # Check the response
        # if not response:
        # die( "Error: Cannot process LE request, no response")
        # if response.status != 200:
        # die( "Error: Cannot process LE request: (%s)"%response.status)


def request(request, required=False, check_status=False, rtype='GET', retry=False):
    """
    Processes a list request on the API server.
    """
    noticed = False
    while True:
        # Obtain response
        response, conn = get_response(rtype, urllib.quote('/' + config.user_key + '/' + request),
                                      die_on_error=not retry)

        # Check the response
        if response:
            break
        if required:
            die('Error: Cannot process LE request, no response')
        if retry:
            if not noticed:
                log.info('Error: No response from LE, re-trying in %ss intervals' % SRV_RECON_TIMEOUT)
                noticed = True
            time.sleep(SRV_RECON_TIMEOUT)
        else:
            return None

    response = response.read()
    conn.close()
    log.debug('List response: %s' % response)
    try:
        d_response = json_loads(response)
    except ValueError:
        die('Error: Invalid response (%s)' % response)

    if check_status and d_response['response'] != 'ok':
        die('Error: %s' % d_response['reason'])

    return d_response


def _startup_info():
    """
    Prints correct startup information based on OS
    """
    if 'darwin' in sys.platform:
        log.info('  sudo launchctl unload /Library/LaunchDaemons/com.logentries.agent.plist')
        log.info('  sudo launchctl load /Library/LaunchDaemons/com.logentries.agent.plist')
    elif 'linux' in sys.platform:
        log.info('  sudo service logentries restart')
    elif 'sunos' in sys.platform:
        log.info('  sudo svcadm disable logentries')
        log.info('  sudo svcadm enable logentries')
    else:
        log.info('')


def request_follow(filename, name, type_opt):
    """
    Creates a new log to follow the file given.
    """
    config.agent_key_required()
    request = {"request": "new_log",
               "user_key": config.user_key,
               "host_key": config.agent_key,
               "name": name,
               "filename": filename,
               "type": type_opt,
               "follow": "true"}
    api_request(request, True, True)
    print "Will follow %s as %s" % (filename, name)
    log.info("Don't forget to restart the daemon")
    _startup_info()


def request_hosts(logs=False):
    """
    Returns list of registered hosts.
    """
    load_logs = 'false'
    if logs:
        load_logs = 'true'
    response = api_request({
                               'request': 'get_user',
                               'load_hosts': 'true',
                               'load_logs': load_logs,
                               'user_key': config.user_key}, True, True)
    return response['hosts']


#
# Commands
#

def cmd_init(args):
    """
    Saves variables given to the configuration file. Variables not
    specified are not saved and thus are overwritten with default value.
    The configuration directory is created if it does not exit.
    """
    no_more_args(args)
    config.user_key_required()
    config.save()
    log.info("Initialized")


def cmd_reinit(args):
    """
    Saves variables given to the configuration file. The configuration
    directory is created if it does not exit.
    """
    no_more_args(args)
    config.load()
    config.save()
    log.info("Reinitialized")


def cmd_register(args):
    """
    Registers the agent in logentries infrastructure. The newly obtained
    agent key is stored in the configuration file.
    """
    no_more_args(args)
    config.load()
    if config.agent_key != NOT_SET and not config.force:
        die("Server already registered. Use --force to override current registration.")
    config.user_key_required()
    config.hostname_required()
    config.name_required()

    si = system_detect(True)

    request = {"request": "register",
               'user_key': config.user_key,
               'name': config.name,
               'hostname': config.hostname,
               'system': si['system'],
               'distname': si['distname'],
               'distver': si['distver']
    }
    response = api_request(request, True, True)

    config.agent_key = response['host_key']
    config.save()

    log.info("Registered %s (%s)" % (config.name, config.hostname))

    # Registering logs
    logs = []
    if config.std or config.std_all:
        logs = collect_log_names(si)
    for logx in logs:
        if config.std_all or logx['default'] == '1':
            request_follow(logx['filename'], logx['name'], logx['type'])


def load_logs():
    """
    Loads logs from the server and initializes followers.
    """
    noticed = False
    logs = None
    while not logs:
        resp = request('hosts/%s/' % config.agent_key, False, False, retry=True)
        if resp['response'] != 'ok':
            if not noticed:
                log.error('Error retrieving list of logs: %s, retrying in %ss intervals' % (
                    resp['reason'], SRV_RECON_TIMEOUT))
                noticed = True
            time.sleep(SRV_RECON_TIMEOUT)
            continue
        logs = resp['list']
        if not logs:
            time.sleep(SRV_RECON_TIMEOUT)

    available_filters = {}
    filter_filenames = default_filter_filenames
    if config.filters != NOT_SET:
        sys.path.append(config.filters)
        try:
            import filters

            available_filters = getattr(filters, 'filters', {})
            filter_filenames = getattr(filters, 'filter_filenames', default_filter_filenames)

            debug_filters("Available filters: %s", available_filters)
            debug_filters("Filter filenames: %s", filter_filenames)
        except:
            log.error('Cannot import event filter module %s: %s', config.filters, sys.exc_info()[1])
            log.error('Details: %s', traceback.print_exc(sys.exc_info()))

    # Start followers
    for l in logs:
        if l['follow'] == 'true':
            log_name = l['name']
            log_filename = l['filename']
            log_key = l['key']

            debug_filters("Log name=%s key=%s filename=%s", log_name, log_key, log_filename)

            # Check filters
            if not filter_filenames(log_filename):
                debug_filters(" Log blocked by filter_filenames, not following")
                log.info('Not following %s, blocked by filter_filenames', log_name)
                continue
            debug_filters(" Looking for filters by name and key")
            event_filter = available_filters.get(log_name)
            if not event_filter:
                debug_filters(" No filter found by name, checking key")
                event_filter = available_filters.get(log_key)
            if event_filter and not hasattr(event_filter, '__call__'):
                debug_filters(" Filter found, but ignored because it's not a function")
                event_filter = None
            if not event_filter:
                event_filter = filter_events
                debug_filters(" No filter found")
            else:
                debug_filters(" Using filter %s", event_filter)

            # Instantiate the follower
            LogFollower(log_filename, log_key, event_filter)


def is_followed(filename):
    """
    Checks if the file given is followed.
    """
    host = request('hosts/%s/' % config.agent_key, True, True)
    logs = host['list']
    for ilog in logs:
        if ilog['follow'] == 'true' and filename == ilog['filename']:
            return True
    return False


def cmd_monitor(args):
    """
    Monitors host activity and sends events collected to logentries infrastructure.
    """
    no_more_args(args)
    config.load()
    if config.agent_key == NOT_SET:
        die('Please register the host first with command `le.py register\'')
    config.agent_key_required()
    config.user_key_required()

    if config.daemon:
        daemonize()

    # Register resource monitoring
    stats = Stats()

    try:
        # Load logs to follow
        if not config.debug_stats_only:
            load_logs()

        # Park this thread
        while True:
            time.sleep(600)  # FIXME: is there a better way?
    except KeyboardInterrupt:
        if stats: stats.cancel()
        set_shutdown()


def cmd_monitor_daemon(args):
    """
    Monitors as a daemon host activity and sends events collected to logentries infrastructure.
    """
    config.daemon = True
    cmd_monitor(args)


def cmd_follow(args):
    """
    Follow the log file given.
    """
    if len(args) == 0:
        die("Error: Specify the file name of the log to follow.")

    config.load()
    config.agent_key_required()

    for arg in args:
        filename = os.path.abspath(arg)
        name = config.name
        if name == NOT_SET:
            name = os.path.basename(filename)
        type_opt = config.type_opt
        if type_opt == NOT_SET:
            type_opt = ""

        # Check that we don't follow that file already
        if not config.force and is_followed(filename):
            log.warning('Already following %s' % filename)

        if len(glob.glob(filename)) == 0:
            log.warning('\nWARNING: File %s does not exist' % filename)

        request_follow(filename, name, type_opt)


def cmd_followed(args):
    """
    Check if the log file given is followed.
    """
    if len(args) == 0:
        die("Error: Specify the file name of the log to test.")
    if len(args) != 1:
        die("Error: Too many arguments. Only one file name allowed.")
    config.load()
    config.agent_key_required()

    filename = os.path.abspath(args[0])

    # Check that we don't follow that file already
    if is_followed(filename):
        print 'Following %s' % filename
        sys.exit(EXIT_OK)
    else:
        print 'NOT following %s' % filename
        sys.exit(EXIT_NO)


def cmd_clean(args):
    """
    Wipes out old configuration file.
    """
    no_more_args(args)
    if config.clean():
        log.info('Configuration clean')


def cmd_whoami(args):
    """
    Displays information about this host.
    """
    config.load()
    config.agent_key_required()
    no_more_args(args)

    list_object(request('hosts/%s' % config.agent_key, True, True))
    print ''
    list_object(request('hosts/%s/' % config.agent_key, True, True))


def get_all_list(what):
    return api_request({"request": "list_" + what,
                        "user_key": config.user_key}, True, True)['list']


def get_all_clusters():
    return get_all_list('clusters')


def get_all_apps():
    return get_all_list('apps')


def get_all_salogs():
    return get_all_list('salogs')


def logtype_name(logtype_uuid):
    response = request('logtypes', True, True)
    all_logtypes = response['list']
    for logtype in all_logtypes:
        if logtype_uuid == logtype['key']:
            return logtype['shortcut']
    return 'unknown'


def list_object(request, hostnames=False):
    """
    Lists object request given.
    """
    t = request['object']
    index_name = 'name'
    item_name = ''
    if t == 'rootlist':
        item_name = 'item'
        pass
    elif t == 'host':
        print 'name =', request['name']
        print 'hostname =', request['hostname']
        print 'key =', request['key']
        print 'distribution =', request['distname']
        print 'distver =', request['distver']
        return
    elif t == 'log':
        print 'name =', request['name']
        print 'filename =', request['filename']
        print 'key =', request['key']
        print 'type =', request['type']
        print 'follow =', request['follow']
        if 'token' in request:
            print 'token =', request['token']
        if 'logtype' in request:
            print 'logtype =', logtype_name(request['logtype'])
        return
    elif t == 'list':
        print 'name =', request['name']
        return
    elif t == 'hostlist':
        item_name = 'host'
        if hostnames:
            index_name = 'hostname'
        pass
    elif t == 'logtype':
        print 'title =', request['title']
        print 'description =', request['desc']
        print 'shortcut =', request['shortcut']
        return
    elif t == 'loglist':
        item_name = 'log'
        pass
    elif t == 'applist':
        item_name = 'app'
        pass
    elif t == 'clusterlist':
        item_name = 'cluster'
        pass
    elif t == 'logtypelist':
        item_name = 'logtype'
        index_name = 'shortcut'
        pass
    else:
        die('Unknown object type "%s". Agent too old?' % t)

    # Standard list, print it sorted
    ilist = request['list']
    ilist = sorted(ilist, key=lambda item: item[index_name])
    for item in ilist:
        if config.uuid:
            print item['key'],
        print "%s" % (item[index_name])
    print_total(ilist, item_name)


def cmd_clusters(args):
    """
    Lists all available clusters.
    """
    no_more_args(args)
    config.load()
    config.user_key_required()
    clusters = get_all_clusters()

    if config.xlist:
        hosts = request_hosts()
        key2host = {}
        for host in hosts:
            key2host[host['key']] = host
        for cluster in clusters:
            chosts = (key2host[chost]['name'] for chost in cluster['list'])
            print "%s  %s" % (cluster['name'], ', '.join(chosts))
    else:
        print ', '.join(cluster['name'] for cluster in clusters)

    print_total(clusters, 'cluster')


def get_cluster_params(args):
    """
    Common code for new and set cluster commands. First parameter is
    a cluster name. Following parameters are host uuids, names, or
    hostnames identifying host to assign. Host names or hostnames
    are converted to uuid.
    """
    if len(args) == 0:
        die("Error: Specify the cluster name.")
    if re.search(r' ', args[0]):
        die("Error: Name must not contain space.")
    config.load()
    config.user_key_required()
    skeys = []
    if len(args) > 1:
        hosts = request_hosts()
        log.debug("Matching hosts to the cluster:")
        for name in args[1:]:
            if len(name) == 0:
                die("Error: Host name is empty.")
            if is_uuid(name):
                skeys.append(name)
                log.debug('\t%s as UUID' % name)
            else:
                # Find name among servers
                matches = find_hosts(name, hosts)
                if len(matches) == 0:
                    die("Error: No host matches '%s'." % name)
                else:
                    log.debug("\t%s:" % name)
                    for h in matches:
                        skeys.append(h['key'])
                        log.debug('\t%s / %s, %s' % (h['key'], h['name'], h['hostname']))
        skeys = uniq(skeys)
        if config.debug:
            log.debug("Adding following hosts:")
            for key in skeys:
                log.debug('\t' + key)
    result = [args[0]]
    result.extend(skeys)
    return result


def cmd_new_cluster(args):
    """
    Creates a new cluster.
    """
    argv = get_cluster_params(args)
    response = api_request({
                               'request': 'new_clusters',
                               'user_key': config.user_key,
                               'names': argv[0]}, True, True)
    cluster_key = response['clusters'][0]['key']
    if len(argv) > 1:
        api_request({
                        'request': 'set_cluster',
                        'cluster_key': cluster_key,
                        'list': ' '.join(argv[1:])}, True, True)
    report("%s cluster registered" % argv[0])


def cmd_set_cluster(args):
    """
    Sets cluster attributes.
    """
    argv = get_cluster_params(args)
    name = argv[0]
    cluster_key = None
    for cluster in get_all_clusters():
        if cluster['name'] == name:
            cluster_key = cluster['key']
            break
    if cluster_key == None:
        die('Error: Cluster with name "%s" not found' % name)

    request = {
        'request': 'set_cluster',
        'cluster_key': cluster_key}
    if config.name:
        name = request['name'] = config.name
    if len(argv) > 1:
        request['list'] = ' '.join(argv[1:])
    api_request(request, True, True)

    report("%s cluster set" % name)


def cmd_apps(args):
    """
    Lists all available apps.
    """
    no_more_args(args)
    config.load()
    config.user_key_required()
    apps = get_all_apps()

    if config.xlist:
        hosts = request_hosts(logs=True)
        key2hostlog = {}
        for host in hosts:
            for xlog in host['logs']:
                key2hostlog[xlog['key']] = host['name'] + ':' + xlog['name']
        for app in apps:
            alogs = (key2hostlog[clog] for clog in app['list'])
            if config.uuid:
                print app['key'],
            print "%s  %s" % (app['name'], ', '.join(alogs))
    else:
        if config.uuid:
            for app in apps:
                print app['key'] + ' ' + app['name']
        else:
            print ', '.join(app['name'] for app in apps)

    print_total(apps, 'app')


def get_app_params(args):
    """
    Common code for new and set app commands. First parameter is an app
    name. Following parameters are log uuids, or server+log names, or
    hostnames identifying log to assign.
    """
    if len(args) == 0:
        die("Error: Specify the app name.")
    if re.search(r' ', args[0]):
        die("Error: Name must not contain space.")
    config.load()
    config.user_key_required()
    skeys = []
    if len(args) > 1:
        hosts = request_hosts(logs=True)
        log.debug("Matching logs to the app:")
        for name in args[1:]:
            if len(name) == 0:
                die("Error: Log name is empty.")
            if is_uuid(name):
                skeys.append(name)
                log.debug('\t%s as UUID' % name)
            else:
                # Find name among servers
                matches = find_logs(name, hosts)
                if len(matches) == 0:
                    die("Error: No log matches '%s'." % name)
                else:
                    log.debug("\t%s:" % name)
                    for l in matches:
                        skeys.append(l['key'])
                        log.debug('\t%s / %s, %s' % (l['key'], l['name'], l['filename']))
        skeys = uniq(skeys)
        if config.debug:
            log.debug("Adding following logs:")
            for key in skeys:
                log.debug('\t' + key)
    result = [args[0]]
    result.extend(skeys)
    return result


def is_log_fs(addr):
    log_addrs = [r'(logs|apps)/.*/',
                 r'host(name)?s/.*/.*/']
    for la in log_addrs:
        if re.match(la, addr):
            return True
    return False


def cmd_new_app(args):
    """
    Creates a new application.
    """
    argv = get_app_params(args)
    response = api_request({
                               'request': 'new_apps',
                               'user_key': config.user_key,
                               'names': argv[0]}, True, True)
    app_key = response['apps'][0]['key']
    if len(argv) > 1:
        api_request({
                        'request': 'set_app',
                        'app_key': app_key,
                        'list': ' '.join(argv[1:])}, True, True)
    report("%s app registered" % argv[0])


def cmd_set_app(args):
    """
    Sets app attributes.
    """
    argv = get_app_params(args)
    name = argv[0]
    app_key = None
    for app in get_all_apps():
        if app['name'] == name:
            app_key = app['key']
            break
    if app_key == None:
        die('Error: App with name "%s" not found' % name)

    request = {
        'request': 'set_app',
        'app_key': app_key}
    if config.name:
        name = request['name'] = config.name
    if len(argv) > 1:
        request['list'] = ' '.join(argv[1:])
    api_request(request, True, True)

    report("%s app set" % name)


def cmd_ls(args):
    """
    General list command
    """
    if len(args) == 0:
        args = ['/']
    config.load()
    config.user_key_required()

    addr = args[0]
    if addr.startswith('/'):
        addr = addr[1:]
    # Make sure we are not downloading log
    if is_log_fs(addr):
        die('Use pull to get log content.')

    # if addr.count('/') > 2:
    # die( 'Path not found')
    list_object(request(addr, True, True), hostnames=addr.startswith('hostnames'))


def cmd_rm(args):
    """
    General remove command
    """
    if len(args) == 0:
        args = ['/']
    config.load()
    config.user_key_required()

    addr = args[0]
    if addr.startswith('/'):
        addr = addr[1:]
    if addr.count('/') > 2:
        die('Path not found')
    response = request(addr, True, True, rtype='DELETE')
    report(response['reason'])


def cmd_pull(args):
    """
    Log pull command
    """
    if len(args) == 0:
        die(PULL_USAGE)
    config.load()
    config.user_key_required()

    params = {}

    addr = args[0]
    if addr.startswith('/'):
        addr = addr[1:]
    if addr.endswith('/'):
        addr = addr[:-1]
    if not is_log_fs(addr + '/'):
        die('Error: Not a log')

    if len(args) > 1:
        time_range = parse_timestamp_range(args[1])
        params['start'] = time_range[0]
        params['end'] = time_range[1]
    if len(args) > 2:
        params['filter'] = args[2]
    if len(args) > 3:
        try:
            params['limit'] = int(args[3])
        except ValueError:
            die('Error: Limit must be integer')

    pull_request(addr, params)


def cmd_push(args):
    """
    Log push command
    """
    if len(args) < 2:
        die(PUSH_USAGE)
    config.load()
    config.user_key_required()

    filename = args[0]

    addr = args[1]
    if addr.startswith('/'):
        addr = addr[1:]
    if addr.endswith('/'):
        addr = addr[:-1]
    if not is_log_fs(addr + '/'):
        die('Error: Not a suitable log path')

    params = {}
    if len(args) > 2:
        params['logtype'] = args[2]

    try:
        data_size = os.path.getsize(filename)
        logfile = open(filename, "r")
    except OSError:
        die("Error: Cannot open '%s'" % filename)
    except IOError:
        die("Error: Cannot open '%s'" % filename)

    push_request(logfile, data_size, addr, params)


#
# Main method
#

def main():
    # Read command line parameters
    args = config.process_params(sys.argv[1:])

    if config.debug:
        log.setLevel(logging.DEBUG)
    if config.debug_system:
        die(system_detect(True))
    if config.debug_loglist:
        die(collect_log_names(system_detect(True)))

    argv0 = sys.argv[0]
    if argv0 and argv0 != '':
        pname = os.path.basename(argv0).split('-')
        if len(pname) != 1:
            args.insert(0, pname[-1])

    if len(args) == 0:
        report(USAGE)
        sys.exit(EXIT_HELP)

    commands = {
        'init': cmd_init,
        'reinit': cmd_reinit,
        'register': cmd_register,
        'monitor': cmd_monitor,
        'monitordaemon': cmd_monitor_daemon,
        'follow': cmd_follow,
        'followed': cmd_followed,
        'clean': cmd_clean,
        'whoami': cmd_whoami,
        # Filesystem operations
        'ls': cmd_ls,
        'rm': cmd_rm,
        'pull': cmd_pull,  # Shortcuts  #'nc': cmd_new_cluster,  #'sc': cmd_set_cluster,  #'na': cmd_new_app,
        # 'sa': cmd_set_app,
    }
    for cmd, func in commands.items():
        if cmd == args[0]:
            return func(args[1:])
    die('Error: Unknown command "%s".' % args[0])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info("Interrupted")


# For Debian Lenny you will need to install ssl:
# aptitude install python-dev libbluetooth-dev
# http://pypi.python.org/pypi/ssl#downloads
# python setup install.py
