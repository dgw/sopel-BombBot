"""
bomb.py - Simple Willie bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from willie.module import ADMIN, commands, event, example, NOLIMIT, rate, require_owner, require_privilege, rule
from random import choice, randint, randrange, sample
from re import search
from threading import Timer
import time
from willie.tools import Identifier
from willie import formatting

# code below relies on colors being at least 3 elements long
colors = ['Red', 'Light_Green', 'Light_Blue', 'Yellow', 'White', 'Black', 'Purple', 'Orange', 'Pink']
fuse = 120  # seconds
fuse_text = '%d minute' % (fuse / 60) if (fuse % 60) == 0 else ('%d second' % fuse)
explosion_text = formatting.color('^!^!^!BOOM!^!^!^', 'red')
bombs = dict()


@commands('bomb')
@rate(600)
@example('.bomb nicky')
def start(bot, trigger):
    """
    Put a bomb in the specified user's pants. They will be kicked if they
     don't guess the right wire fast enough.
    """
    if not trigger.group(3):
        bot.say('Who do you want to bomb?')
        return NOLIMIT
    if not trigger.sender.startswith('#'):
        bot.say('You can only bomb someone in a channel.')
        return NOLIMIT
    global bombs
    target = Identifier(trigger.group(3))
    if target == bot.nick:
        bot.say('You thought you could trick me into bombing myself?!')
        return NOLIMIT
    if target.lower() in bombs:
        bot.say('I can\'t fit another bomb in ' + target + '\'s pants!')
        return NOLIMIT
    if target == trigger.nick:
        bot.say('%s pls. Bomb a friend if you have to!' % trigger.nick)
        return NOLIMIT
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.say('You can\'t bomb imaginary people!')
        return NOLIMIT
    if bot.db.get_nick_value(Identifier(target), 'unbombable') and not trigger.admin:
        bot.say('I\'m not allowed to bomb %s, sorry.' % target)
        return NOLIMIT
    wires = [ colors[i] for i in sorted(sample(xrange(len(colors)), randrange(3,5))) ]
    num_wires = len(wires)
    wires_list = [ formatting.color( str(wire), str(wire) ) for wire in wires ]
    wires_list = ", ".join(wires_list[:-2] + [" and ".join(wires_list[-2:])]).replace('Light_', '')
    wires = [ wire.replace('Light_', '') for wire in wires ]
    color = choice(wires)
    message = 'Hey, %s! I think there\'s a bomb in your pants. %s timer, %d wires: %s. ' \
              'Which wire would you like to cut? (respond with %scutwire color)' \
              % ( target, fuse_text, num_wires, wires_list, bot.config.core.help_prefix or '.' )
    bot.say(message)
    bot.notice("Hey, don't tell %s, but it's the %s wire." % (target, color), trigger.nick)
    timer = Timer(fuse, explode, (bot, trigger))
    bombs[target.lower()] = (wires, color, timer, target)
    timer.start()


@commands('cutwire')
@example('.cutwire red')
def cutwire(bot, trigger):
    """
    Tells willie to cut a wire when you've been bombed.
    """
    global bombs
    if trigger.is_privmsg:
        return
    target = Identifier(trigger.nick)
    if target.lower() != bot.nick.lower() and target.lower() not in bombs:
        bot.say('You can\'t cut a wire until someone bombs you, ' + target)
        return
    if not trigger.group(2):
        bot.say('You have to choose a wire to cut.')
        return
    # Remove target from bomb list temporarily
    wires, color, timer, orig_target = bombs.pop(target.lower())
    wirecut = trigger.group(2).rstrip(' ')
    if wirecut.lower() in ('all', 'all!'):
        timer.cancel()  # defuse timer, execute premature detonation
        bot.say('Cutting ALL the wires! (You should\'ve picked the %s wire.)' % color)
        if bot.db.get_channel_value(trigger.sender, 'bomb_kicks'):
            kmsg = 'KICK %s %s :%s' % (trigger.sender, target, explosion_text)
            bot.write([kmsg])
        else:
            bot.say('%s is dead! %s' % (target, explosion_text))
        alls = bot.db.get_nick_value(target, 'bomb_alls') or 0
        bot.db.set_nick_value(target, 'bomb_alls', alls + 1)
    elif wirecut.capitalize() not in wires:
        bot.say('That wire isn\'t here, ' + target + '! You sure you\'re picking the right one?')
        # Add the target back onto the bomb list
        bombs[target.lower()] = (wires, color, timer, orig_target)
    elif wirecut.capitalize() == color:
        bot.say('You did it, ' + target + '! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
        timer.cancel()  # defuse bomb
        defuses = bot.db.get_nick_value(target, 'bomb_defuses') or 0
        bot.db.set_nick_value(target, 'bomb_defuses', defuses + 1)
    else:
        timer.cancel()  # defuse timer, execute premature detonation
        bot.say('Nope, wrong wire! Aww, now you\'ve gone and killed yourself. Wow. Sorry. (You should\'ve picked the %s wire.)' % color)
        if bot.db.get_channel_value(trigger.sender, 'bomb_kicks'):
            kmsg = ('KICK %s %s :%s' % (trigger.sender, target, explosion_text))
            bot.write([kmsg])
        else:
            bot.say('%s is dead! %s' % (target, explosion_text))
        wrongs = bot.db.get_nick_value(target, 'bomb_wrongs') or 0
        bot.db.set_nick_value(target, 'bomb_wrongs', wrongs + 1)


def explode(bot, trigger):
    target = Identifier(trigger.group(3))
    if target.lower() not in bombs: # nick change happened
        for nick in bombs.keys():
            if bombs[nick][3] == target:
                target = Identifier(nick)
                break
    bot.say('%s pls, you could\'ve at least picked one! Now you\'re dead. You see that? Guts, all over the place.' \
        ' (You should\'ve picked the %s wire.)' % (target, bombs[target.lower()][1]) )
    if bot.db.get_channel_value(trigger.sender, 'bomb_kicks'):
        kmsg = ('KICK %s %s :%s' % (trigger.sender, target, explosion_text))
        bot.write([kmsg])
    else:
        bot.say('%s is dead! %s' % (target, explosion_text))
    bombs.pop(target.lower())
    timeouts = bot.db.get_nick_value(target, 'bomb_timeouts') or 0
    bot.db.set_nick_value(target, 'bomb_timeouts', timeouts + 1)


# Track nick changes
@event('NICK')
@rule('.*')
def bomb_glue(bot, trigger):
    old = trigger.nick
    new = Identifier(trigger)
    if old.lower() in bombs:
        bombs[new.lower()] = bombs.pop(old.lower())


@commands('bombstats')
@example('.bombstats')
@example('.bombstats myfriend')
def bombstats(bot, trigger):
    """
    Get bomb stats for yourself or another user.
    """
    if not trigger.group(2):
        target = Identifier(trigger.nick)
    else:
        target = Identifier(trigger.group(2))
    wrongs = bot.db.get_nick_value(target, 'bomb_wrongs') or 0
    timeouts = bot.db.get_nick_value(target, 'bomb_timeouts') or 0
    defuses = bot.db.get_nick_value(target, 'bomb_defuses') or 0
    alls = bot.db.get_nick_value(target, 'bomb_alls') or 0
    total = wrongs + timeouts + defuses + alls
    # short-circuit if user has no stats
    if total == 0:
        msg = 'Nobody bombed %s yet!' % target
        if target != trigger.nick:
            msg += ' Maybe you should be the first, %s. =3' % trigger.nick
        bot.say(msg)
        return
    wrongs += alls # merely a presentation decision
    # grammar shit
    g_wrongs = 'time' if wrongs == 1 else 'times'
    g_timeouts = 'attempt' if timeouts == 1 else 'attempts'
    g_defuses = 'bomb' if defuses == 1 else 'bombs'
    g_alls = 'was' if alls == 1 else 'were'
    msg = '%s defused %d %s, but failed %d %s and didn\'t even bother with %d %s.' \
           % (target, defuses, g_defuses, wrongs, g_wrongs, timeouts, g_timeouts)
    if alls:
        msg += ' (%d of the failures %s from not giving a fuck and cutting ALL the wires!)' % (alls, g_alls)
    bot.say(msg)


@commands('bombstatreset')
@example('.bombstatreset spammer')
@require_owner('Only the bot owner can reset bomb stats')
def statreset(bot, trigger):
    """
    Reset a given user's bomb stats (e.g. after abuse)
    """
    if not trigger.group(2):
        bot.say('Whose bomb stats do you want me to reset?')
        return
    target = trigger.group(2)
    keys = ['bomb_wrongs', 'bomb_defuses', 'bomb_timeouts', 'bomb_alls']
    for key in keys:
        bot.db.set_nick_value(target, key, 0)
    bot.say('Bomb stats for %s reset.' % target)


@commands('bomboff')
@example('.bomboff')
def exclude(bot, trigger):
    """
    Disable bombing yourself (admins: or another user)
    """
    if not trigger.group(2):
        target = trigger.nick
    else:
        target = Identifier(trigger.group(2))
    if not trigger.admin and target != trigger.nick:
        bot.say('Only bot admins can exclude other users.')
        return
    bot.db.set_nick_value(target, 'unbombable', True)
    bot.say('Marked %s as unbombable.' % target)


@commands('bombon')
@example('.bombon')
def unexclude(bot, trigger):
    """
    Re-enable bombing yourself (admins: or another user)
    """
    if not trigger.group(2):
        target = trigger.nick
    else:
        target = Identifier(trigger.group(2))
    if not trigger.admin and target != trigger.nick:
        bot.say('Only bot admins can unexclude other users.')
        return
    bot.db.set_nick_value(target, 'unbombable', False)
    bot.say('Marked %s as bombable again.' % target)


@commands('bombkickoff')
@example('.bombkickoff')
@require_privilege(ADMIN, "Only a channel admin or greater can disable bomb kicks.")
def nokick(bot, trigger):
    """
    Allows channel admins and up to disable kicking for bombs in the channel.
    """
    if trigger.is_privmsg:
        return
    bot.db.set_channel_value(trigger.sender, 'bomb_kicks', False)
    bot.say('Bomb kicks disabled in %s.' % trigger.sender)


@commands('bombkickon')
@example('.bombkickon')
@require_privilege(ADMIN, "Only a channel admin or greater can enable bomb kicks.")
def yeskick(bot, trigger):
    """
    Allows channel admins and up to (re-)enable kicking for bombs in the channel.
    """
    if trigger.is_privmsg:
        return
    bot.db.set_channel_value(trigger.sender, 'bomb_kicks', True)
    bot.say('Bomb kicks enabled in %s.' % trigger.sender)


@commands('bombnickmerge')
@require_owner()
@example('.bombnickmerge newbie into old_friend')
def is_really(bot, trigger):
    """
    Merge the two nicks, keeping the stats for the second one.
    """
    duplicate = trigger.group(3) or None
    primary = trigger.group(5) or None
    if not primary or not duplicate or trigger.group(4).lower() != 'into':
        bot.reply("I want to be sure there are no mistakes here. Please specify nicks to merge " \
                  "as: <duplicate> into <primary>")
        return
    duplicate = Identifier(duplicate)
    primary = Identifier(primary)
    newstats = dict()
    for stat in ('bomb_wrongs', 'bomb_timeouts', 'bomb_defuses', 'bomb_alls'):
        dupval = bot.db.get_nick_value(duplicate, stat) or 0
        prival = bot.db.get_nick_value(primary, stat) or 0
        newstats[stat] = dupval + prival
    for stat in newstats:
        bot.db.set_nick_value(primary, stat, newstats[stat])
        bot.db.set_nick_value(duplicate, stat, 0) # because willie < 6.0 doesn't merge properly
    bot.db.merge_nick_groups(primary, duplicate)
    bot.say('Merged %s into %s.' % (duplicate, primary))

