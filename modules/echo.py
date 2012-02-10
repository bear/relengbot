#!/usr/bin/env python

""" RelEng IRC Bot - echo module

    :copyright: (c) 2012 by Mozilla
    :license: MPLv2

    Authors:
        bear    Mike Taylor <bear@mozilla.com>
"""


def echo(msg, sender, channel, private, irc):
    irc.tell(channel, 'echo [%s]' % msg)
echo.commands = ['echo', "foo"]