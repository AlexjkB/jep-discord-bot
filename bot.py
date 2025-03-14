import discord
from discord.ext import tasks, commands
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
answer_lock = True
channel = None

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

def check_answer(guess):
    global answer
    global scores
    if guess.lower().replace(' ','') == answer.lower().replace(' ',''):
        return True
    return False

##################################################
@tasks.loop(seconds=8.0, count=1)
async def clue_loop():
    global answer_lock
    global clue
    global answer
    global category
    global value
    global channel
    answer_lock = False
    new_clue()
    text = category + ' for $' + value + '\n'
    text += clue
    await channel.send(text)

@clue_loop.after_loop
async def after_clue_loop():
    global state
    if state == State.Playing:
        answer_loop.start()

@tasks.loop(seconds=2.0, count=1)
async def answer_loop():
    global answer_lock
    global answer
    global channel
    answer_lock = True
    text = 'Answer: ' + answer
    await channel.send(text)

@answer_loop.after_loop
async def after_answer_loop():
    global state
    if state == State.Playing:
        clue_loop.start()


    

##################################################

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    global state
    global scores
    global clue
    global answer
    global category
    global value
    global channel
    global answer_lock
    
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
            clue_loop.cancel()
            answer_loop.cancel()
            answer_lock = True
            return
        else:
            if not answer_lock:
                account = message.author.name
                if check_answer(message.content):
                    if account not in scores:
                        scores[account] = int(value)
                    else:
                        scores[account] += int(value)
                    text = account + ' got the answer correct!'
                    await message.channel.send(text)
                    clue_loop.cancel()
                    answer_loop.start()
                else:
                    if account not in scores:
                        scores[account] = 0 - int(value)
                    else:
                        scores[account] -= int(value)
    
    if state == State.Stopped:
        if message.content.startswith('!play'):
            channel = message.channel
            state = State.Playing
            clue_loop.start()
            return

client.run(TOKEN)
