"""
bomb.py - Simple Willie bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from willie.module import commands,rule,require_admin
from random import choice, randint
from re import search
import sched
import time
from willie.tools import Identifier

# code below relies on colors being at least 3 elements long
colors = ['Red', 'Green', 'Blue', 'Yellow', 'White', 'Black']
num_colors = len(colors)
color_list = ", ".join(colors[:-2] + [" and ".join(colors[-2:])]) # using too few colors will break this; see above
# eventually this should be a config thing that can be edited while the bot is running...
sch = sched.scheduler(time.time, time.sleep)
fuse = 120  # seconds
timer = '%d minute' % (fuse / 60) if (fuse % 60) == 0 else ('%d second' % fuse)
bombs = dict()


@commands('bomb')
def start(bot, trigger):
    """
    Put a bomb in the specified user's pants. They will be kicked if they
     don't guess the right wire fast enough.
    """
    if not trigger.group(3):
        bot.say('Who do you want to bomb?')
        return
    if not trigger.sender.startswith('#'):
        bot.say('You can only bomb someone in a channel.')
        return
    global bombs
    global sch
    target = Identifier(trigger.group(3))
    if target == bot.nick:
        bot.say('You thought you could trick me into bombing myself?!')
        return
    if target.lower() in bombs:
        bot.say('I can\'t fit another bomb in ' + target + '\'s pants!')
        return
    if target == trigger.nick:
        bot.say('%s pls. Bomb a friend if you have to!' % trigger.nick)
        return
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.say('You can\'t bomb imaginary people!')
        return
    if bot.db.get_nick_value(Identifier(target), 'unbombable'):
        bot.say('I\'m not allowed to bomb %s, sorry.' % target)
        return
    message = 'Hey, %s! I think there\'s a bomb in your pants. %s timer, %d wires: %s. ' \
              'Which wire should I cut? (respond with @cutwire color)' \
              % ( target, timer, num_colors, color_list )
    bot.say(message)
    color = choice(colors)
    bot.notice("Hey, don't tell %s, but it's the %s wire." % (target, color), trigger.nick)
    code = sch.enter(fuse, 1, explode, (bot, trigger))
    bombs[target.lower()] = (color, code)
    sch.run()


@commands('cutwire')
def cutwire(bot, trigger):
    """
    Tells willie to cut a wire when you've been bombed.
    """
    global bombs, colors
    target = Identifier(trigger.nick)
    if target.lower() != bot.nick.lower() and target.lower() not in bombs:
        bot.say('You can\'t cut a wire until someone bombs you, ' + target)
        return
    if not trigger.group(2):
        bot.say('You have to choose a wire to cut.')
        return
    color, code = bombs.pop(target.lower())  # remove target from bomb list
    wirecut = trigger.group(2).rstrip(' ')
    if wirecut.lower() in ('all', 'all!'):
        sch.cancel(code)  # defuse timer, execute premature detonation
        bot.say('Cutting ALL the wires! (You should\'ve picked the %s wire.)' % color)
        kmsg = ('KICK %s %s :^!^!^!BOOM!^!^!^' % (trigger.sender, target))
        bot.write([kmsg])
    elif wirecut.capitalize() not in colors:
        bot.say('That wire isn\'t here, ' + target + '! You sure you\'re picking the right one?')
        bombs[target.lower()] = (color, code)  # Add the target back onto the bomb list,
    elif wirecut.capitalize() == color:
        bot.say('You did it, ' + target + '! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
        sch.cancel(code)  # defuse bomb
    else:
        sch.cancel(code)  # defuse timer, execute premature detonation
        bot.say('Nope, wrong wire! Aww, now you\'ve gone and killed yourself. Wow. Sorry. (You should\'ve picked the %s wire.)' % color)
        kmsg = 'KICK %s %s :^!^!^!BOOM!^!^!^' % (trigger.sender, target)
        bot.write([kmsg])


def explode(bot, trigger):
    target = Identifier(trigger.group(3))
    bot.say('%s pls, you could\'ve at least picked one! Now you\'re dead. You see that? Guts, all over the place.' \
        ' (You should\'ve picked the %s wire.)' % (target, bombs[target.lower()][0]) )
    kmsg = 'KICK %s %s :^!^!^!BOOM!^!^!^' % (trigger.sender, target)
    bot.write([kmsg])
    bombs.pop(target.lower())


@rule('$nickdon\'t bomb (.+)')
def exclude(bot, trigger):
    target = Identifier(trigger.group(1))
    if not trigger.admin and target != 'me':
        bot.say('Only bot admins can exclude other users.')
        return
    if target == 'me':
        target = Identifier(trigger.nick)
    bot.db.set_nick_value(target, 'unbombable', True)
    bot.say('Marked %s as unbombable.' % target)


@rule('$nickyou can bomb (.+)')
def unexclude(bot, trigger):
    target = Identifier(trigger.group(1))
    if not trigger.admin and target != 'me':
        bot.say('Only bot admins can unexclude other users.')
        return
    if target == 'me':
        target = Identifier(trigger.nick)
    bot.db.set_nick_value(target, 'unbombable', False)
    bot.say('Marked %s as bombable again.' % target)

