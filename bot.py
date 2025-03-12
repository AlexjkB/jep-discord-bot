import discord
import os
import requests
import json
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

## updates clue and corresponding info
def new_clue():
    global clue
    global answer
    global category
    global value
    try:
        response = requests.get(CLUE_API).json()
        clue = response['clue_question']
        answer = response['clue_answer']
        category = response['clue_category']
        temp = response['clue_value']
        if temp == 'DD' or temp == 'FINAL':
            new_clue()
        else:
            value = str(temp.replace('$',''))
    except:
        print('Error here bruh')
        clue = 'Error getting clue from API.'
        answer = ''
        category = 'Error'
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

    if state == State.Playing:
        if message.content.startswith('!stop'):
            state = State.Stopped
            return
        else:
            ''' handle answer attempts'''
    
    if state == State.Stopped:
        if message.content.startswith('!play'):
            state = State.Playing
            return

client.run(TOKEN)
