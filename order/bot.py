import telepot

bot = telepot
me_id = 30029482465
telebot = bot.Bot('5452641067:AAGJ4whio6iS9jYs0qaadTL1UqNojCY3h8A')


def massage(txt):
    telebot.sendMessage(me_id, txt, parse_mode="Markdown")