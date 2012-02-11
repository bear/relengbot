RelEng Bot

Python based IRC bot (yes, I know) that gives an IRC interface to
various Mozilla Release Engineering systems.

Super simple Module system that is designed to be easy to write
modules for, not to be efficient or super-snazzy fancy.

Module Framework

Modules are standalone python files that receive messages from
the main IRC loop.  Once called, the command function should do
everything needed and perform any replies.  

Yep, currently modules are sequential, so if your module is slow
then the whole bot will appear sluggish.

Two sample modules are in the modules directory: echo.py and ping.py

Needed Modules:

buildduty
  reply with the person currently on buildduty
  allow buildduty to change via bot
  (optional) set buildduty schedule via bot

reboot slave

enable/disable slave
  reach into slavealloc and mark a slave as enabled/disabled
  (?) require a reason why and record it in slavealloc

status
  query slave to return:
      enabled?
      slavealloc notes
      last 5 jobs run and their status
      what master it's on

health
  query slave via ping, ssh and other methods to ensure that it is
  up and running

time
  return current time, or if TZ given, time in that timezone

nagios
  a filter to monitor nagios that checks if a slave has a note or is disabled
  and if so, ack that alert in nagios

scan puppet and master log items in redis for errors and alert them


TODO
  add get/set key store for modules
  add hooks to redis so filters can be triggered against external events
    (logs, time, ???)

