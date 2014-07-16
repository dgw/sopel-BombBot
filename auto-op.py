import willie

SOP = ["EmmaK","BrokenRobot","Shaun_Away","Shaun","Myst_Waker","Karamazov","slothified"]
Founder = ["johnlage"]

@willie.module.rule(".*")
@willie.module.event("JOIN")
def auto_op(bot,trigger):
    if not trigger.sender.is_nick():
        if not trigger.nick == bot.nick:
            if trigger.nick in Founder:
                bot.write(['MODE', trigger.sender, "+qo", trigger.nick, trigger.nick])
            elif trigger.nick in SOP:
                bot.write(['MODE', trigger.sender, "+ao", trigger.nick, trigger.nick])
        else:
            for nick in bot.privileges[trigger.sender.lower()]:
                if nick in Founder:
                    bot.write(['MODE', trigger.sender, "+qo", nick, nick])
                elif nick in SOP:
                    bot.write(['MODE', trigger.sender, "+ao", nick, nick])


@willie.module.commands("auto","auto-op")
def auto_op_on_command(bot,trigger):
    if not trigger.sender.is_nick():
        for nick in bot.privileges[trigger.sender.lower()]:
            if nick in Founder:
                bot.write(['MODE', trigger.sender, "+qo", nick, nick])
            elif nick in SOP:
                bot.write(['MODE', trigger.sender, "+ao", nick, nick])
        bot.reply("Auto-op Completed Successfully")
