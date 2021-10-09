import os
import discord
from dotenv import dotenv_values
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

config = {
    **dotenv_values(".env"),
    **os.environ,
}
bot = commands.Bot(command_prefix='!', intents=intents)
MESSAGE_DELETE_AFTER: int = 5


@bot.command(name='roster')
@commands.has_role('[RM] Leads')
async def roster(ctx, action: str, user: discord.Member, role: discord.Role):
    actions = ("ajouter", "supprimer")
    action = action.lower()

    if action in actions:
        if not role.name.startswith("[Raids] Roster"):
            await ctx.message.channel.send('Seuls les rôles des rosters peuvent être utilisés avec cette commande.', delete_after=MESSAGE_DELETE_AFTER)
        else:
            if role in user.roles:
                if action == actions[0]:
                    await ctx.message.channel.send(f'{user} a déjà le rôle "{role.name}".', delete_after=MESSAGE_DELETE_AFTER)
                elif action == actions[1]:
                    await user.remove_roles(role)
                    await ctx.message.channel.send(f'Rôle "{role.name}" supprimé pour {user}.', delete_after=MESSAGE_DELETE_AFTER)
                    await user.send(f'{ctx.message.author} t\'a retiré le rôle "{role.name}" sur le serveur "{ctx.message.guild.name}".')
            else:
                if action == actions[0]:
                    await user.add_roles(role)
                    await ctx.message.channel.send(f'Rôle "{role.name}" ajouté à {user}.', delete_after=MESSAGE_DELETE_AFTER)
                    await user.send(f'{ctx.message.author} t\'a donné le rôle "{role.name}" sur le serveur "{ctx.message.guild.name}".')
                elif action == actions[1]:
                    await ctx.message.channel.send(f'{user} n\'a pas le rôle "{role.name}".', delete_after=MESSAGE_DELETE_AFTER)
    else:
        actions_text = ', '.join(actions)
        await ctx.message.channel.send(f"Les actions possibles sont : {actions_text}.", delete_after=MESSAGE_DELETE_AFTER)

    await ctx.message.delete()


@bot.command(name='ga-reset')
@commands.has_role('Admin LBM')
async def giveaway_reset(ctx):
    role = discord.utils.get(ctx.message.guild.roles, name=config['DISCORD_ROLE_GIVEAWAY'])

    if len(role.members) > 0:
        total = 0
        for user in role.members:
            await user.remove_roles(role)
            total = total + 1

        await ctx.message.channel.send(f'Rôle "{role}" réinitialisé ({total}).', delete_after=MESSAGE_DELETE_AFTER)
    else:
        await ctx.message.channel.send(f'Aucune personne avec le "{role}" à réinitialiser.', delete_after=MESSAGE_DELETE_AFTER)

    await ctx.message.delete()


@bot.command(name='composter')
@commands.has_role('Organisateur d\'événements')
async def composter(ctx):

    if ctx.message.author.voice is None:
        await ctx.message.channel.send(':thinking: Tu n\'es pas connecté·e a un salon vocal...', delete_after=MESSAGE_DELETE_AFTER)
    else:
        role_giveaway = discord.utils.get(ctx.message.guild.roles, name=config['DISCORD_ROLE_GIVEAWAY'])
        role_ticket_neuf = discord.utils.get(ctx.message.guild.roles, name='Ticket neuf')
        tickets_neufs = []

        for user in ctx.message.author.voice.channel.members:
            roles = user.roles

            if role_giveaway not in roles:
                await user.add_roles(role_giveaway)

            if role_ticket_neuf in roles:
                if user.nick is not None:
                    name = user.nick
                else:
                    name = f"{user.name}#{user.discriminator}"
                tickets_neufs.append(name)

        tickets_max = len(tickets_neufs)
        if tickets_max > 0:
            tickets_neufs_text = "\n— ".join(tickets_neufs)
            channel = bot.get_channel(int(config['DISCORD_CHANNEL_TICKETS']))
            await channel.send(f":tickets: **Tickets à valider :**\n— {tickets_neufs_text}")
            await ctx.message.channel.send(f':tada: Ta demande de validation de tickets a bien été envoyée ! ({tickets_max})', delete_after=MESSAGE_DELETE_AFTER)
        else:
            await ctx.message.channel.send('Aucun ticket neuf à valider !', delete_after=MESSAGE_DELETE_AFTER)

    await ctx.message.delete()


@bot.event
async def on_command_error(ctx, error):
    await ctx.message.channel.send(f":warning: Error: {error}", delete_after=MESSAGE_DELETE_AFTER)


@bot.event
async def on_ready():
    print('Ready!')


bot.run(config['DISCORD_BOT_TOKEN'])
