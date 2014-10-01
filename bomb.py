"""
bomb.py - Simple Willie bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from willie.module import commands
from random import choice, randint
from re import search
import sched
import time
from willie.tools import Nick
colors = ['Red', 'Yellow', 'Blue', 'White', 'Black']
sch = sched.scheduler(time.time, time.sleep)
fuse = 120  # seconds
bombs = dict()


@commands('bomb')
def start(bot, trigger):
    """
    Put a bomb in the specified user's pants. They will be kicked if they
     don't guess the right wire fast enough.
    """
    if not trigger.group(3):
        bot.say('Who do you want to Bomb?')
        return
    if not trigger.sender.startswith('#'):
        bot.say('Tell me this in a channel')
        return
    global bombs
    global sch
    target = Nick(trigger.group(3))
    if target == bot.nick:
        bot.say('I will NOT BOMB MYSELF!')
        return
    if target.lower() in bombs:
        bot.say('I can\'t fit another bomb in ' + target + '\'s pants!')
        return
    if target == trigger.nick:
        bot.say('I will not LET YOU BOMB YOURSELF!')
        return
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.say('Please Bomb someone WHO IS HERE!')
        return
    message = 'Hey, ' + target + '! Don\'t look but, I think there\'s a bomb in your pants. 2 minute timer, 5 wires: Red, Yellow, Blue, White and Black. Which wire should I cut? Don\'t worry, I know what I\'m doing! (respond with .cutwire color)'
    bot.say(message)
    color = choice(colors)
    bot.msg(trigger.nick,
               "Hey, don\'t tell %s, but the %s wire? Yeah, that\'s the one."
               " But shh! Don\'t say anything!" % (target, color))
    code = sch.enter(fuse, 1, explode, (bot, trigger))
    bombs[target.lower()] = (color, code)
    sch.run()


@commands('cutwire')
def cutwire(bot, trigger):
    """
    Tells willie to cut a wire when you've been bombed.
    """
    global bombs, colors
    target = Nick(trigger.nick)
    if target.lower() != bot.nick.lower() and target.lower() not in bombs:
        bot.say('You can\'t cut a wire till someone bombs you')
        return
    color, code = bombs.pop(target.lower())  # remove target from bomb list
    wirecut = trigger.group(2).rstrip(' ')
    if wirecut.lower() in ('all', 'all!'):
        sch.cancel(code)  # defuse timer, execute premature detonation
        kmsg = ('KICK %s %s : Cutting ALL the wires! *boom* (You should\'ve picked the %s wire.)'
                % (trigger.sender, target, color))
        bot.write([kmsg])
    elif wirecut.capitalize() not in colors:
        bot.say('I can\'t seem to find that wire, ' + target + '! You sure you\'re picking the right one? It\'s not here!')
        bombs[target.lower()] = (color, code)  # Add the target back onto the bomb list,
    elif wirecut.capitalize() == color:
        bot.say('You did it, ' + target + '! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
        sch.cancel(code)  # defuse bomb
    else:
        sch.cancel(code)  # defuse timer, execute premature detonation
        kmsg = 'KICK ' + trigger.sender + ' ' + target + \
               ' : No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry. (You should\'ve picked the ' + color + ' wire.)'
        bot.write([kmsg])


def explode(bot, trigger):
    target = Nick(trigger.group(3))
    kmsg = 'KICK ' + trigger.sender + ' ' + target + \
           ' : Oh, come on, ' + target + '! You could\'ve at least picked one! Now you\'re dead. Guts, all over the place. You see that? Guts, all over YourPants. (You should\'ve picked the ' + bombs[target.lower()][0] + ' wire.)'
    bot.write([kmsg])
    bombs.pop(target.lower())

#Test
