#!/usr/bin/env python

"""
    :copyright: (c) 2012 by Mozilla
    :license: MPLv2
"""

import os, sys
import time
import json
import logging
import traceback

from optparse import OptionParser
from logging.handlers import RotatingFileHandler
from multiprocessing import get_logger, log_to_stderr

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, all_events


log      = get_logger()
_ourPath = os.getcwd()
_ourName = os.path.splitext(os.path.basename(sys.argv[0]))[0]


def relativeDelta(td):
    s = ''
    if td.days < 0:
        t = "%s ago"
    else:
        t = "in %s"

    days    = abs(td.days)
    seconds = abs(td.seconds)
    minutes = seconds / 60
    hours   = minutes / 60
    weeks   = days / 7
    months  = days / 30
    years   = days / 365

    if days == 0:
        if seconds < 20:
            s = 'just now'
        if seconds < 60:
            s = '%d seconds' % seconds
            s = t % s
        if seconds < 120:
            s = t % 'a minute'
        if seconds < 3600:
            s = '%d minutes' % minutes
            s = t % s
        if seconds < 7200:
            s = t % 'an hour'
        if seconds < 86400:
            s = '%d hours' % hours
            s = t % s
    else:
        if days == 1:
            if td.days < 0:
                s = 'yesterday'
            else:
                s = 'tomorrow'
        elif days < 7:
            s = '%d days' % days
            s = t % s
        elif days < 31:
            s = '%d weeks' % weeks
            s = t % s
        elif days < 365:
            s = '%d months' % months
            s = t % s
        else:
            s = '%d years' % years
            s = t % s

    return s

def loadConfig(filename):
    result = {}
    if os.path.isfile(filename):
        try:
            result = json.loads(' '.join(open(filename, 'r').readlines()))
        except:
            log.warning('error during loading of config file [%s]' % filename, exc_info=True)
    return result

def initOptions(defaults=None):
    """Parse command line parameters and populate the options object.
    """
    parser = OptionParser()

    if defaults is not None:
        for key in defaults:
            items = defaults[key]

            if len(items) == 4:
                (shortCmd, longCmd, defaultValue, helpText) = items
                optionType = 's'
            else:
                (shortCmd, longCmd, defaultValue, helpText, optionType) = items

            if optionType == 'b':
                parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
            else:
                parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

    (options, args) = parser.parse_args()
    options.args    = args

    options.appPath = _ourPath

    if options.config is not None:
        options.config = os.path.abspath(options.config)

        if not os.path.isfile(options.config):
            options.config = os.path.join(_ourPath, '%s.cfg' % options.config)

        if not os.path.isfile(options.config):
            options.config = os.path.abspath(os.path.join(_ourPath, '%s.cfg' % _ourName))

        jsonConfig = loadConfig(options.config)

        for key in jsonConfig:
            setattr(options, key, jsonConfig[key])

    if options.logpath is not None:
        options.logpath = os.path.abspath(options.logpath)

        if os.path.isdir(options.logpath):
            options.logfile = os.path.join(options.logpath, '%s.log'% _ourName)
        else:
            options.logfile = None

    if 'background' not in defaults:
        options.background = False

    return options

def initLogs(options):
    if options.logpath is not None:
        fileHandler   = RotatingFileHandler(os.path.join(options.logpath, '%s.log' % _ourName), maxBytes=1000000, backupCount=99)
        fileFormatter = logging.Formatter('%(asctime)s %(levelname)-7s %(processName)s: %(message)s')

        fileHandler.setFormatter(fileFormatter)

        log.addHandler(fileHandler)
        log.fileHandler = fileHandler

    if not options.background:
        echoHandler   = logging.StreamHandler()
        echoFormatter = logging.Formatter('%(levelname)-7s %(processName)s: %(message)s')

        echoHandler.setFormatter(echoFormatter)

        log.addHandler(echoHandler)
        log.info('echoing')

    if options.debug:
        log.setLevel(logging.DEBUG)
        log.info('debug level is on')
    else:
        log.setLevel(logging.INFO)

class rbot(SingleServerIRCBot):
    def __init__(self, config, trigger='!', cb=None):
        self.active       = False
        self.joined       = False
        self.registerNick = False
        self.callback     = cb
        self.starttime    = time.strftime('%H:%M on %A, %d %B', time.gmtime(time.time()) )

        self.nickname   = config.nickname
        self.password   = config.password
        self.chanlist   = config.channels
        self.server     = config.server
        self.port       = config.port
        self.trigger    = config.trigger
        self.nicklength = len(self.nickname)
        self.realname   = self.nickname

        SingleServerIRCBot.__init__(self, [(self.server, self.port)], self.nickname, self.realname, ssl=True)

    def start(self):
        self._connect()
        self.active = True

    def stop(self):
        self.active = False
        self.ircobj.disconnect_all()

    def process(self):
        self.ircobj.process_once(0.5)

    def tell(self, target, message):
        self.connection.privmsg(target, message)

    def do_join(self, event, cmd, data):
        # print 'join: ' + data[1] + ' '  + data[2]
        SingleServerIRCBot._on_join(self, self.connection, event)
        self.connection.join(data[1], data[2])

    def do_part(self, event, cmd, data):
        pass
        # print 'part: %s %s' % (data[1], data[2])

    def on_ctcp(self, serverconnection, event):
        if event.arguments()[0] == 'ACTION':
            event.arguments().pop(0)
            self.on_action(serverconnection, event)
        elif event.arguments()[0] == 'VERSION':
            serverconnection.ctcp_reply(nm_to_n(event.source()), version)
        elif event.arguments()[0] == 'PING':
            if len(event.arguments()) > 1:
                serverconnection.ctcp_reply(nm_to_n(event.source()), 'PING ' + event.arguments()[1])

    def on_action(self, serverconnection, event):
        pass
        # print 'action: %s|%s|%s' % (nm_to_n(event.source()), str(event.arguments()), event.eventtype())

    def on_privmsg(self, serverconnection, event):
        if self.callback is not None:
            sender  = nm_to_n(event.source())
            channel = event.target()
            self.callback(event.arguments()[0], sender, channel, True, self)

    def on_pubmsg(self, serverconnection, event):
        if self.callback is not None:
            sender  = nm_to_n(event.source())
            channel = event.target()
            self.callback(event.arguments()[0], sender, channel, False, self)

    def on_welcome(self, serverconnection, event):
        print 'welcome: %s' % self.server

        if len(self.chanlist) == 0:
            print 'welcome: no channels configured -- stopping'
            self.stop()
        else:
            if self.registerNick:
                print 'registering with nickserv'
                self.registerNick = False
                self.tell('nickserv', 'identify %s' % self.password)
                time.sleep(0.5)

            for chan in self.chanlist:
                if '|' in chan:
                    chan, pw = chan.split('|')
                else:
                    pw = ""
                print 'joining %s %s' % (chan, pw)
                serverconnection.join(chan, pw)

    def on_join(self, serverconnection, event):
        self.joined = True
        chan        = event.target().lower()

        if chan not in self.chanlist:
            self.chanlist.append(chan)

    def on_part(self, serverconnection, event):
        if event.target() in self.chanlist:
            self.chanlist.remove(event.target())

        self.joined = (len(self.chanlist) > 0)

    def on_quit(self, serverconnection, event):
        if nm_to_n(event.source()) == self.nickname:
            self.joined = False

    def on_list(self, serverconnection, event):
        if len(event.arguments()) > 2:
            ch = event.arguments()[0]
            n  = event.arguments()[1]
            self.stats[ch] = n

