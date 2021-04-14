import discord
from discord.ext import commands
import sys
import re

import quiz

bot = commands.Bot(command_prefix = '!', description = '')
bot.quiz = quiz.Quiz()

async def checkrights(ctx, required):
    passed = False
    if required == "admin":
        if ctx.message.author.id == bot.admin:
            passed = True
    elif required == "moderator":
        if ctx.message.author.id == bot.admin or ctx.message.author in bot.moderators:
            passed = True

    # elif ctx.message.author.id in bot.quiz.scores.keys():
    #     author_type = "player"
    # else:
    #     author_type = "other"

    if not passed:
        await ctx.send(f"Désolé <@!{ctx.message.author.id}>, tu n'as pas les droits nécessaires.")

    return passed


@bot.event
async def on_ready():
    print('Logged in as: ' + bot.user.name)
    print('User ID: ' + str(bot.user.id))
    print(bot.admin)
    print('------')

@bot.command()
async def logoff(ctx):
    if await checkrights(ctx, "admin"):
        await ctx.send('Leaving server. BYE!')
        await bot.close()
        exit()

@bot.command()
async def hello(ctx):
    await ctx.send(f'Bonjour <@!{ctx.message.author.id}>, je suis l\'animateur du Cogni\'Quiz !')

@bot.command()
async def stop(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.stop(ctx)

@bot.command()
async def reset(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.reset()

@bot.command()
async def start(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.start(ctx)

@bot.command()
async def scores(ctx):
    await bot.quiz.print_scores(ctx)

@bot.command()
async def editscore(ctx, user: discord.User, new_score):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.edit_score(ctx, user, new_score)

@bot.command()
async def conclude(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.conclude_question(ctx)

@bot.command()
async def next(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.next_question(ctx)

@bot.command()
async def skip(ctx):
    if await checkrights(ctx, "moderator"):
        await bot.quiz.skip_question(ctx)

@bot.command()
async def addmoderator(ctx, user: discord.User):
    if await checkrights(ctx, "admin"):
        bot.moderators.add(user)
        await ctx.send(f'<@!{user.id}> est maintenant modérateur.rice.')

@bot.command()
async def editadmin(ctx, user: discord.User):
    if await checkrights(ctx, "admin"):
        bot.admin = user.id
        await ctx.send(f'<@!{user.id}> est maintenant mon administrateur.rice.')

@bot.command()
async def removemoderator(ctx, user: discord.User):
    if await checkrights(ctx, "admin"):
        bot.moderators.discard(user)
        await ctx.send(f'<@!{user.id}> n\'est plus modérateur.rice.')

@bot.command()
async def showrights(ctx):
    if await checkrights(ctx, "admin"):
        await ctx.send(f'<@!{bot.admin}> est mon administrateur.rice.')
        if len(bot.moderators) > 0:
            await ctx.send("Les modérateurs.rices sont: ")
            for user in bot.moderators:
                await ctx.send(f'<@!{user.id}>')

@bot.command(aliases=['a'])
async def answer(ctx):
    if bot.quiz is not None and bot.quiz.started():
        #check if we have a question pending
        await bot.quiz.answer_question(ctx)
        #check quiz question correct


#run the program!
if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print('Usage: python bot.py APP_BOT_USER_TOKEN ADMIN_ID')
        exit()
        
    # logs into channel    
    try:
        bot.admin = int(sys.argv[2])
        bot.moderators = set({})
        bot.run(sys.argv[1])

    except:        
        bot.close()