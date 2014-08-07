import willie

SOP = ["EmmaK","BrokenRobot","Shaun_Away","Shaun","Myst_Waker","slothified","iamnotharrypott","squid","dgw"]
Founder = ["johnlage","johnlage_away"]

@willie.module.rule(".*")
@willie.module.event("JOIN")
def auto_op(bot,trigger):
    if not trigger.sender.is_nick():
        if not trigger.nick == bot.nick:
            if trigger.nick in Founder:
                bot.write(['MODE', trigger.sender, "+qao", trigger.nick, trigger.nick, trigger.nick])
            elif trigger.nick in SOP:
                bot.write(['MODE', trigger.sender, "+ao", trigger.nick, trigger.nick])
        else:
            for nick in bot.privileges[trigger.sender.lower()]:
                if nick in Founder:
                    bot.write(['MODE', trigger.sender, "+qao", nick, nick, nick])
                elif nick in SOP:
                    bot.write(['MODE', trigger.sender, "+ao", nick, nick])

@willie.module.rule(".*")
@willie.module.event("NICK")
def auto_op_nick_change(bot,trigger):
    old_nick = bot.origin.nick
    new_nick = bot.origin.sender    
    if new_nick in Founder:
        for channel in bot.channels:
            bot.write(['MODE', channel, "+qao", new_nick, new_nick, new_nick])
    elif new_nick in SOP:
        for channel in bot.channels:
            bot.write(['MODE', channel, "+ao", new_nick, new_nick])


@willie.module.commands("auto","auto-op")
def auto_op_on_command(bot,trigger):
    if not trigger.sender.is_nick():
        for nick in bot.privileges[trigger.sender.lower()]:
            if nick in Founder:
                bot.write(['MODE', trigger.sender, "+qao", nick, nick, nick])
            elif nick in SOP:
                bot.write(['MODE', trigger.sender, "+ao", nick, nick])
        bot.reply("Auto-op Completed Successfully")

@willie.module.commands("down")
def op_down(bot,trigger):
    if not trigger.sender.is_nick():
        if trigger.nick in Founder:
            bot.write(['MODE', trigger.sender, "-qao", trigger.nick, trigger.nick, trigger.nick])
        elif trigger.nick in SOP:
            bot.write(['MODE', trigger.sender, "-ao", trigger.nick, trigger.nick])

@willie.module.commands("up")
def op_up(bot,trigger):
    if not trigger.sender.is_nick():
        if trigger.nick in Founder:
            bot.write(['MODE', trigger.sender, "+qao", trigger.nick, trigger.nick, trigger.nick])
        elif trigger.nick in SOP:
            bot.write(['MODE', trigger.sender, "+ao", trigger.nick, trigger.nick])
