import discord
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()
TOKEN = os.getenv("BOT_KEY")
CLUE_API = os.getenv("CLUE")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

##################################################

class State(Enum):
    Stopped = 1
    Playing = 2

state = State.Stopped

scores = {}

clue = ''
answer= ''
category = ''
value = 0

##################################################

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):

    ## Ignore messages the bot has sent.
    if message.author == client.user:
        return

    ## Display scores at any moment
    if message.content.startswith('!score'):
        if scores:
            text = 'SCORES \n'
            for player in scores:
                text = text + player + ': ' + str(scores[player]) + '\n'
            await message.channel.send(text)  
        else:
            await message.channel.send('No scores at the moment.')
        return 

    ## Display all commands at any moment 
    if message.content.startswith('!help'):
        text = 'ALL COMMANDS \n'
        text += '\'!help\'    - Displays all commands. \n'
        text += '\'!play\'    - Starts the game. \n'
        text += '\'!stop\'    - Stops the game. \n'
        text += '\'!scores\'  - Stops the game. \n'
        await message.channel.send(text)
        return 

    if state = State.Playing:
        if message.content.startswith('!stop'):
            state = State.Stopped
            return
        else:
            ''' handle answer attempts'''
    
    '''TODO - !play and !stop'''

client.run(TOKEN)
