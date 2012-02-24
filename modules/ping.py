#!/usr/bin/env python

""" RelEng IRC Bot - ping module

    :copyright: (c) 2012 by Mozilla
    :license: MPLv2

    Authors:
        bear    Mike Taylor <bear@mozilla.com>
"""

import subprocess


def runCommand(cmd, env=None):
    """Execute the given command.
    Sends to the logger all stdout and stderr output.
    """
    o = []
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    try:
        for item in p.stdout:
            o.append(item[:-1])
        p.wait()
    except KeyboardInterrupt:
        p.kill()
        p.wait()

    return p, o


def ping(msg, sender, channel, private, irc):
    args = msg.split(' ')
    if len(args) > 0:
        reply = []
        for host in args:
            p, o = runCommand(['ping', '-c 5', '-o', host])

            # bash-3.2$ ping -c 2 -o tegra-056
            # PING tegra-056.build.mtv1.mozilla.com (10.250.49.43): 56 data bytes
            # 64 bytes from 10.250.49.43: icmp_seq=0 ttl=64 time=1.119 ms
            # 
            # --- tegra-056.build.mtv1.mozilla.com ping statistics ---
            # 1 packets transmitted, 1 packets received, 0.0% packet loss
            # round-trip min/avg/max/stddev = 1.119/1.119/1.119/0.000 ms

            for s in o:
                if '1 packets transmitted, 1 packets received' in s:
                    reply.append('%s: %s' % (host, s))
                    break
        if len(reply) > 0:
            irc.put(('irc', channel, '\n'.join(reply)))
ping.commands = ['ping']