"""
bomb.py - Simple Sopel bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import division, unicode_literals
from sopel.module import *
from sopel.tools import Identifier
from sopel import formatting
from random import choice, randrange, sample
from threading import Timer, RLock
import sys
import time

# 2 to 3 stuff; should be replaced by six probably
if sys.version_info.major > 2:
    xrange = range

# code below relies on colors being at least 3 elements long
COLORS = ['Red', 'Light_Green', 'Light_Blue', 'Yellow', 'White', 'Black', 'Purple', 'Orange', 'Pink']
FUSE = 120  # seconds
TIMEOUT = 600

STRINGS = {
    'FUSE':                   "%d minute" % (FUSE // 60) if (FUSE % 60) == 0 else ("%d second" % FUSE),
    'TARGET_MISSING':         "Who do you want to bomb?",
    'CHANNEL_DISABLED':       "An admin has disabled bombing in %s.",
    'TIMEOUT_REMAINING':      "You must wait %.0f seconds before you can bomb someone again.",
    'TARGET_BOT':             "You thought you could trick me into bombing myself?!",
    'TARGET_SELF':            "%s pls. Bomb a friend if you have to!",
    'TARGET_IMAGINARY':       "You can't bomb imaginary people!",
    'TARGET_DISABLED':        "I'm not allowed to bomb %s, sorry.",
    'TARGET_DISABLED_FYI':    "Just so you know, %s is marked as unbombable.",
    'NOT_WHILE_DISABLED':     "Try again when you're bombable yourself, %s.",
    'TARGET_FULL':            "I can't fit another bomb in %s's pants!",
    'BOMB_PLANTED':           ["Hey, %(target)s! I think there's a bomb in your pants. %(fuse_time)s timer, "
                               "%(wire_num)d wires: %(wire_list)s. Which wire would you like to cut? "
                               "(respond with %(prefix)scutwire color)",
                               "%(target)s, I just saw someone put a bomb down your pants! There are %(wire_num)d "
                               "wires (%(wire_list)s), and I think it's a %(fuse_time)s fuse. Quick, tell me what "
                               "wire to cut! (respond with %(prefix)scutwire color)",
                               "\u306d, %(target)s, there's a stowaway in your pants. It's a bomb on a %(fuse_time)s "
                               "timer. Given where it is, you should probably let me cut one of the %(wire_num)d wires "
                               "for you. The colors are %(wire_list)s. (respond with %(prefix)scutwire color)"],
    'BOMB_ANSWER':            "Hey, don't tell %s, but it's the %s wire.",
    'CUT_NO_BOMB':            "You can't cut a wire until someone bombs you, %s.",
    'CUT_NO_WIRE':            "You have to choose a wire to cut.",
    'CUT_ALL_WIRES':          "Cutting ALL the wires! (You should've picked the %s wire.)",
    'CUT_IMAGINARY':          "That wire isn't here, %s! You sure you're picking the right one?",
    'CUT_CORRECT':            "You did it, %s! I'll be honest, I thought you were dead. "
                              "But nope, you did it. You picked the right one. Well done.",
    'CUT_WRONG':              "Nope, wrong wire! Aww, now you've gone and killed yourself. "
                              "Wow. Sorry. (You should've picked the %s wire.)",
    'NEVER_TRIED':            "%s pls, you could've at least picked one! Now you're dead. You see that? "
                              "Guts, all over the place. (You should've picked the %s wire.)",
    'EXPLOSION':              formatting.color("^!^!^!BOOM!^!^!^", 'red'),
    'TARGET_DEAD':            "%s is dead! %s",
    'CANCEL_WHOM':            "Please specify whose bomb to cancel.",
    'CANCEL_NO_BOMB':         "There is no bomb on %s.",
    'CANCEL_NO_PERMISSION':   "You don't have permission to cancel %s's bomb!",
    'CANCEL_DONE':            "Cancelled %s's bomb.",
    'BOMB_STILL':             "There's still a bomb in your pants, %s!",
    'NOT_BOMBED':             "Nobody bombed %s yet!",
    'MAYBE_YOU':              " Maybe you should be the first, %s. =3",
    'BOMBS_PLANTED':          " Bombs planted: %d",
    'BOMB_STATS':             "%s defused %d %s, but failed %d %s and didn't even bother with %d %s.",
    'ALLS_STATS':             " (%d of the failures %s from not giving a fuck and cutting ALL the wires!)",
    'SUCCESS_RATE':           " Success rate: %.1f%%",
    'RESET_WHO':              "Whose bomb stats do you want me to reset?",
    'RESET_DONE':             "Bomb stats for %s reset.",
    'RECENTLY_PLANTED':       "You recently planted a bomb, and must remain bombable for %.0f more seconds.",
    'ADMINS_MARK_UNBOMBABLE': "Only bot admins can exclude other users.",
    'MARKED_UNBOMBABLE':      "Marked %s as unbombable.",
    'ADMINS_MARK_BOMBABLE':   "Only bot admins can unexclude other users.",
    'MARKED_BOMBABLE':        "Marked %s as bombable again.",
    'OP_DISABLE_KICKS':       "Only a channel operator or greater can disable bomb kicks.",
    'KICKS_DISABLED':         "Bomb kicks disabled in %s.",
    'OP_ENABLE_KICKS':        "Only a channel operator or greater can enable bomb kicks.",
    'KICKS_ENABLED':          "Bomb kicks enabled in %s.",
    'ADMIN_DISABLE_BOMBS':    "Only a channel admin or greater can disable bombing in this channel.",
    'BOMBS_DISABLED':         "Bombs disabled in %s.",
    'ADMIN_ENABLE_BOMBS':     "Only a channel admin or greater can enable bombing in this channel.",
    'BOMBS_ENABLED':          "Bombs enabled in %s.",
}

BOMBS = {}
lock = RLock()


@commands('bomb')
@example(".bomb nicky")
@require_chanmsg
def start(bot, trigger):
    """
    Put a bomb in the specified user's pants. If they take too long or guess wrong,
     they die (and get kicked from the channel, if enabled).
    """
    if not trigger.group(3):
        bot.say(STRINGS['TARGET_MISSING'])
        return NOLIMIT
    if bot.db.get_channel_value(trigger.sender, 'bombs_disabled'):
        bot.notice(STRINGS['CHANNEL_DISABLED'] % trigger.sender, trigger.nick)
        return NOLIMIT
    since_last = time_since_bomb(bot, trigger.nick)
    if since_last < TIMEOUT and not trigger.admin:
        bot.notice(STRINGS['TIMEOUT_REMAINING'] % (TIMEOUT - since_last),
                   trigger.nick)
        return
    global BOMBS
    target = Identifier(trigger.group(3))
    target_unbombable = bot.db.get_nick_value(target, 'unbombable')
    if target == bot.nick:
        bot.say(STRINGS['TARGET_BOT'])
        return NOLIMIT
    if is_self(bot, trigger.nick, target):
        bot.say(STRINGS['TARGET_SELF'] % trigger.nick)
        return NOLIMIT
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.say(STRINGS['TARGET_IMAGINARY'])
        return NOLIMIT
    if target_unbombable and not trigger.admin:
        bot.say(STRINGS['TARGET_DISABLED'] % target)
        return NOLIMIT
    if bot.db.get_nick_value(trigger.nick, 'unbombable'):
        bot.say(STRINGS['NOT_WHILE_DISABLED'] % trigger.nick)
        return NOLIMIT
    with lock:
        if target.lower() in BOMBS:
            bot.say(STRINGS['TARGET_FULL'] % target)
            return NOLIMIT
        wires = [COLORS[i] for i in sorted(sample(xrange(len(COLORS)), randrange(3, 5)))]
        num_wires = len(wires)
        wires_list = [formatting.color(str(wire), str(wire)) for wire in wires]
        wires_list = ", ".join(wires_list[:-2] + [" and ".join(wires_list[-2:])]).replace('Light_', '')
        wires = [wire.replace('Light_', '') for wire in wires]
        color = choice(wires)
        bot.say(
                choice(STRINGS['BOMB_PLANTED']) % {'target':           target,
                                                   'fuse_time': STRINGS['FUSE'],
                                                   'wire_num':         num_wires,
                                                   'wire_list':        wires_list,
                                                   'prefix':           bot.config.core.help_prefix or '.'
                                                   })
        bot.notice(STRINGS['BOMB_ANSWER'] % (target, color), trigger.nick)
        if target_unbombable:
            bot.notice(STRINGS['TARGET_DISABLED_FYI'] % target, trigger.nick)
        timer = Timer(FUSE, explode, (bot, trigger))
        BOMBS[target.lower()] = {'wires':  wires,
                                 'color':  color,
                                 'timer':  timer,
                                 'target': target,
                                 'bomber': trigger.nick
                                 }
        timer.start()
    bombs_planted = bot.db.get_nick_value(trigger.nick, 'bombs_planted') or 0
    bot.db.set_nick_value(trigger.nick, 'bombs_planted', bombs_planted + 1)
    bot.db.set_nick_value(trigger.nick, 'bomb_last_planted', time.time())


@commands('cutwire')
@example(".cutwire red")
@require_chanmsg
def cutwire(bot, trigger):
    """
    Tells sopel to cut a wire when you've been bombed.
    """
    global BOMBS
    target = Identifier(trigger.nick)
    if target == bot.nick:  # a parallel bot behind a bouncer (e.g. Bucket) can trigger this function (see #16)
        return
    with lock:
        if target.lower() != bot.nick.lower() and target.lower() not in BOMBS:
            bot.say(STRINGS['CUT_NO_BOMB'] % target)
            return
        if not trigger.group(3):
            bot.say(STRINGS['CUT_NO_WIRE'])
            return
        # Remove target from bomb list temporarily
        bomb = BOMBS.pop(target.lower())
        wirecut = trigger.group(3)
        if wirecut.lower() in ('all', 'all!'):
            bomb['timer'].cancel()  # defuse timer, execute premature detonation
            bot.say(STRINGS['CUT_ALL_WIRES'] % bomb['color'])
            kickboom(bot, trigger, target)
            alls = bot.db.get_nick_value(bomb['target'], 'bomb_alls') or 0
            bot.db.set_nick_value(bomb['target'], 'bomb_alls', alls + 1)
        elif wirecut.capitalize() not in bomb['wires']:
            bot.say(STRINGS['CUT_IMAGINARY'] % target)
            # Add the target back onto the bomb list
            BOMBS[target.lower()] = bomb
        elif wirecut.capitalize() == bomb['color']:
            bot.say(STRINGS['CUT_CORRECT'] % target)
            bomb['timer'].cancel()  # defuse bomb
            defuses = bot.db.get_nick_value(bomb['target'], 'bomb_defuses') or 0
            bot.db.set_nick_value(bomb['target'], 'bomb_defuses', defuses + 1)
        else:
            bomb['timer'].cancel()  # defuse timer, execute premature detonation
            bot.say(STRINGS['CUT_WRONG'] % bomb['color'])
            kickboom(bot, trigger, target)
            wrongs = bot.db.get_nick_value(bomb['target'], 'bomb_wrongs') or 0
            bot.db.set_nick_value(bomb['target'], 'bomb_wrongs', wrongs + 1)


@commands('bombcancel', 'cancelbomb')
@example('.bombcancel unfortunateuser')
@require_chanmsg
def cancel_bomb(bot, trigger):
    """
    Cancel the bomb placed on the specified player (can also be used by admins).
    """
    target = trigger.group(3) or None
    if not target:
        bot.reply(STRINGS['CANCEL_WHOM'])
        return
    target = Identifier(target)  # issue #24
    with lock:
        if target.lower() not in BOMBS:
            bot.reply(STRINGS['CANCEL_NO_BOMB'] % target)
            return
        if trigger.nick != BOMBS[target.lower()]['bomber'] and not trigger.admin:
            bot.reply(STRINGS['CANCEL_NO_PERMISSION'] % target)
            return
        bomber = BOMBS[target.lower()]['bomber']
        bombs_planted = bot.db.get_nick_value(bomber, 'bombs_planted') or 0
        bot.db.set_nick_value(bomber, 'bombs_planted', bombs_planted - 1)
        BOMBS.pop(target.lower())['timer'].cancel()
        bot.say(STRINGS['CANCEL_DONE'] % target)


# helper functions
def explode(bot, trigger):
    target = Identifier(trigger.group(3))
    orig_target = target
    with lock:
        if target.lower() not in BOMBS:  # nick change happened
            for nick in BOMBS.keys():
                if BOMBS[nick]['target'] == target:
                    target = Identifier(nick)
                    break
        bot.say(STRINGS['NEVER_TRIED'] % (target, BOMBS[target.lower()]['color']))
        kickboom(bot, trigger, target)
        BOMBS.pop(target.lower())
    timeouts = bot.db.get_nick_value(orig_target, 'bomb_timeouts') or 0
    bot.db.set_nick_value(orig_target, 'bomb_timeouts', timeouts + 1)


def kickboom(bot, trigger, target):
    if bot.db.get_channel_value(trigger.sender, 'bomb_kicks') and not bot.db.get_nick_value(target, 'unbombable'):
        kmsg = "KICK %s %s :%s" % (trigger.sender, target, STRINGS['EXPLOSION'])
        bot.write([kmsg])
    else:
        bot.say(STRINGS['TARGET_DEAD'] % (target, STRINGS['EXPLOSION']))


def time_since_bomb(bot, nick):
    now = time.time()
    last = bot.db.get_nick_value(nick, 'bomb_last_planted') or 0
    return abs(last - now)


def is_self(bot, nick, target):
    nick = Identifier(nick)
    target = Identifier(target)
    if nick == target:
        return True  # shortcut to catch common goofballs
    try:
        nick_id = bot.db.get_nick_id(nick, False)
        target_id = bot.db.get_nick_id(target, False)
    except ValueError:
        return False  # if either nick doesn't have an ID, they can't be in a group
    return nick_id == target_id


# Track nick changes
@event('NICK')
@rule('.*')
def bomb_glue(bot, trigger):
    old = trigger.nick
    new = Identifier(trigger)
    with lock:
        if old.lower() in BOMBS:
            BOMBS[new.lower()] = BOMBS.pop(old.lower())
            bot.notice(STRINGS['BOMB_STILL'] % new, new)


@commands('bombstats', 'bombs')
@example(".bombstats")
@example(".bombs myfriend")
def bombstats(bot, trigger):
    """
    Get bomb stats for yourself or another user.
    """
    if not trigger.group(3):
        target = Identifier(trigger.nick)
    else:
        target = Identifier(trigger.group(3))
    wrongs = bot.db.get_nick_value(target, 'bomb_wrongs') or 0
    timeouts = bot.db.get_nick_value(target, 'bomb_timeouts') or 0
    defuses = bot.db.get_nick_value(target, 'bomb_defuses') or 0
    alls = bot.db.get_nick_value(target, 'bomb_alls') or 0
    total = wrongs + timeouts + defuses + alls
    planted = bot.db.get_nick_value(target, 'bombs_planted') or 0
    # short-circuit if user has no stats
    if total == 0:
        msg = STRINGS['NOT_BOMBED'] % target
        if target != trigger.nick:
            msg += STRINGS['MAYBE_YOU'] % trigger.nick
        if planted:
            msg += STRINGS['BOMBS_PLANTED'] % planted
        bot.say(msg)
        return
    success_rate = defuses / total * 100
    wrongs += alls  # merely a presentation decision
    # grammar shit
    g_wrongs = "time" if wrongs == 1 else "times"
    g_timeouts = "attempt" if timeouts == 1 else "attempts"
    g_defuses = "bomb" if defuses == 1 else "bombs"
    g_alls = "was" if alls == 1 else "were"
    msg = STRINGS['BOMB_STATS'] % (target, defuses, g_defuses, wrongs, g_wrongs, timeouts, g_timeouts)
    if alls:
        msg += STRINGS['ALLS_STATS'] % (alls, g_alls)
    msg += STRINGS['SUCCESS_RATE'] % success_rate
    if planted:
        msg += STRINGS['BOMBS_PLANTED'] % planted
    bot.say(msg)


@commands('bombstatreset')
@example(".bombstatreset spammer")
@require_owner('Only the bot owner can reset bomb stats')
def statreset(bot, trigger):
    """
    Reset a given user's bomb stats (e.g. after abuse)
    """
    if not trigger.group(3):
        bot.say(STRINGS['RESET_WHO'])
        return
    target = Identifier(trigger.group(3))
    keys = ['bomb_wrongs', 'bomb_defuses', 'bomb_timeouts', 'bomb_alls', 'bombs_planted']
    for key in keys:
        bot.db.set_nick_value(target, key, 0)
    bot.say(STRINGS['RESET_DONE'] % target)


@commands('bomboff')
@example(".bomboff")
def exclude(bot, trigger):
    """
    Disable bombing yourself (admins: or another user)
    """
    if not trigger.group(3):
        target = trigger.nick
        time_since = time_since_bomb(bot, target)
        if time_since < TIMEOUT:
            bot.notice(STRINGS['RECENTLY_PLANTED'] % (TIMEOUT - time_since), target)
            return
    else:
        target = Identifier(trigger.group(3))
    if not trigger.admin and target != trigger.nick:
        bot.say(STRINGS['ADMINS_MARK_UNBOMBABLE'])
        return
    bot.db.set_nick_value(target, 'unbombable', True)
    bot.say(STRINGS['MARKED_UNBOMBABLE'] % target)


@commands('bombon')
@example(".bombon")
def unexclude(bot, trigger):
    """
    Re-enable bombing yourself (admins: or another user)
    """
    if not trigger.group(3):
        target = trigger.nick
    else:
        target = Identifier(trigger.group(3))
    if not trigger.admin and target != trigger.nick:
        bot.say(STRINGS['ADMINS_MARK_BOMBABLE'])
        return
    bot.db.set_nick_value(target, 'unbombable', False)
    bot.say(STRINGS['MARKED_BOMBABLE'] % target)


@commands('bombkickoff')
@example(".bombkickoff")
@require_privilege(OP, STRINGS['OP_DISABLE_KICKS'])
@require_chanmsg
def nokick(bot, trigger):
    """
    Allows channel admins and up to disable kicking for bombs in the channel.
    """
    bot.db.set_channel_value(trigger.sender, 'bomb_kicks', False)
    bot.say(STRINGS['KICKS_DISABLED'] % trigger.sender)


@commands('bombkickon')
@example(".bombkickon")
@require_privilege(OP, STRINGS['OP_ENABLE_KICKS'])
@require_chanmsg
def yeskick(bot, trigger):
    """
    Allows channel admins and up to (re-)enable kicking for bombs in the channel.
    """
    bot.db.set_channel_value(trigger.sender, 'bomb_kicks', True)
    bot.say(STRINGS['KICKS_ENABLED'] % trigger.sender)


@commands('bombsoff')
@example(".bombsoff")
@require_privilege(ADMIN, "")
@require_chanmsg
def bombnazi(bot, trigger):
    """
    Allows channel admins and up to disable bombing entirely in the current channel.
    """
    bot.db.set_channel_value(trigger.sender, 'bombs_disabled', True)
    bot.say(STRINGS['BOMBS_DISABLED'] % trigger.sender)


@commands('bombson')
@example(".bombson")
@require_privilege(ADMIN, STRINGS['ADMIN_ENABLE_BOMBS'])
@require_chanmsg
def bomboprah(bot, trigger):
    """
    Allows channel admins and up to (re-)enable bombing in the current channel.
    """
    bot.db.set_channel_value(trigger.sender, 'bombs_disabled', False)
    bot.say(STRINGS['BOMBS_ENABLED'] % trigger.sender)
