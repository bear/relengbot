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

from multiprocessing import Process, get_logger, log_to_stderr

from irc import initOptions, initLogs, rbot


log      = get_logger()
commands = {}
filters  = []


def processMessage(msg, sender, channel, private, irc):
    print u'%s:%s %s' % (channel, sender, msg)

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
        if cmd in commands:
            commands[cmd](' '.join(args[1:]), sender, channel, private, irc)
    else:
        for cmd, func in filters:
            func(msg, sender, channel, private, irc)


def processIRC(options):
    filenames = []

    ircBot = rbot(options, cb=processMessage)
    ircBot.start()

    for filename in os.listdir(options.modules):
        if filename.endswith('.py') and not filename.startswith('_'):
            filenames.append(os.path.join(options.modules, filename))

    for filename in filenames:
       fname = os.path.basename(filename)[:-3]
       try: module = imp.load_source(fname, filename)
       except:
          log.error('Unable to load module %s' % fname, exc_info=True)
       else:
          if hasattr(module, 'setup'):
             module.setup(self)
          for item, obj in vars(module).iteritems():
              if hasattr(obj, 'commands'):
                  for cmd in obj.commands:
                      commands[cmd] = obj
              if hasattr(obj, 'filters'):
                  for cmd in obj.filters:
                      filters.append((cmd, obj))

    while ircBot.active:
        ircBot.process()


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

    Process(target=processIRC, args=(options,)).start()

