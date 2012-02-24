#!/usr/bin/env python

""" RelEng IRC Bot

    :copyright: (c) 2012 by Mozilla
    :license: MPLv2

    Assumes Python v2.6+

    Usage
        -c --config         Configuration file (json format)
                            default: ./rbot.cfg
        -d --debug          Turn on debug logging
                            default: False
        -l --logpath        Path where the log file output is written
                            default: None
        -b --background     Fork to a daemon process
                            default: False

    Authors:
        bear    Mike Taylor <bear@mozilla.com>
"""

import sys, os
import imp
import logging

from multiprocessing import Process, Queue, get_logger, log_to_stderr
from Queue import Empty

from irc import initOptions, initLogs, rbot


log         = get_logger()
ircQueue    = Queue()
ircModules  = {}
ircCommands = {}
ircFilters  = []


def loadModules(options):
    filenames = []

    for filename in os.listdir(options.modules):
        if filename.endswith('.py') and not filename.startswith('_'):
            filenames.append(os.path.join(options.modules, filename))

    for filename in filenames:
        fname = os.path.basename(filename)[:-3]

        q = Queue()
        p = Process(target=handleModule, name=fname, args=(fname, filename, q, ircQueue, options))
        ircModules[fname] = { 'process': p,
                              'queue':   q,
                            }
        p.start()


def handleModule(moduleName, filename, qMsg, qIRC, options):
    log.info('initializing modue %s [%s]' % (moduleName, filename))

    try:
        commands = {}
        filters  = []
        module   = imp.load_source(moduleName, filename)

        if hasattr(module, 'setup'):
            log.info('calling setup for %s' % moduleName)
            module.setup(self)

        for item, obj in vars(module).iteritems():
            if hasattr(obj, 'commands'):
                for cmd in obj.commands:
                    log.info('registering command %s' % cmd)
                    qIRC.put(('command', moduleName, cmd))
                    commands[cmd] = obj
            if hasattr(obj, 'filters'):
                for cmd in obj.filters:
                    log.info('registering filter %s' % cmd)
                    qIRC.put(('filter', moduleName))
                    filters.append(obj)

    except:
        module = None
        log.error('Unable to load module %s' % moduleName, exc_info=True)
        qIRC.put(('module', 'remove', moduleName))

    if module is not None:
        while True:
            try:
                item = qMsg.get(False)
            except Empty:
                item = None

            if item is not None:
                cmd, msg, sender, channel, private = item
                log.info('processing %s' % cmd)
                if cmd == 'filter':
                    for func in filters:
                        func(msg, sender, channel, private, qIRC)
                else:
                    commands[cmd](msg, sender, channel, private, qIRC)


def processMessage(msg, sender, channel, private, irc):
    log.info(u'%s:%s %s' % (channel, sender, msg))

    args = msg.split(' ', 1)
    cmd  = None
    if args[0].startswith(irc.trigger):
        cmd = args[0][1:]
        body = ' '.join(args[1:])
    else:
        if (len(args) > 1) and (args[0] == irc.nickname):
            cmd  = args[1]
            body = ' '.join(args[2:])

    if cmd is not None:
        if cmd in ircCommands:
            mod = ircCommands[cmd]
            log.info('send msg to module %s for command %s' % (mod, cmd))
            ircModules[mod]['queue'].put((cmd, ' '.join(args[1:]), sender, channel, private))
    else:
        for mod in ircFilters:
            log.info('send msg to module %s for filter' % mod)
            ircModules[mod]['queue'].put(('filter', msg, sender, channel, private))



_defaultOptions = { 'config':      ('-c', '--config',     './rbot.cfg', 'Configuration file'),
                    'debug':       ('-d', '--debug',      True,         'Enable Debug', 'b'),
                    'background':  ('-b', '--background', False,        'daemonize ourselves', 'b'),
                    'logpath':     ('-l', '--logpath',    None,         'Path where log file is to be written'),
                    'modules':     ('-m', '--modules',    './modules',  'Path where bot modules are found'),
                  }

if __name__ == "__main__":
    options = initOptions(_defaultOptions)
    initLogs(options)

    log.info('Starting')

    loadModules(options)

    ircBot = rbot(options, cb=processMessage)
    ircBot.start()

    while ircBot.active:
        ircBot.process()

        try:
            msg = ircQueue.get(False)
        except Empty:
            msg = None

        if msg is not None:
            if msg[0] == 'irc':
                ircBot.tell(msg[1], msg[2])
            elif msg[0] == 'command':
                log.info('registering %s %s' % (msg[0], msg[2]))
                ircCommands[msg[2]] = msg[1]
            elif msg[0] == 'filter':
                log.info('registering %s %s' % (msg[0], msg[1]))
                ircFilters.append(msg[1])

