import discord
from discord.ext import tasks, commands
import os
import requests
from dotenv import load_dotenv
from enum import Enum
from itertools import combinations
import copy
import re
import Levenshtein

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
        clue = 'Error getting clue from API.'
        answer = ''
        category = 'Error'
        value = 0

# code inspired by protobowl checker2
equivalence_list = [
    ['zero', 'zeroeth', 'zeroth', '0'],
    ['one', 'first', 'i', '1', '1st'],
    ['two', 'second', 'ii', '2', '2nd'],
    ['three', 'third', 'iii', 'turd', '3', '3rd'],
    ['four', 'forth', 'fourth', 'iv', '4', '4th'],
    ['fifth', 'five', '5', '5th', 'v', 'versus', 'vs', 'against'],
    ['sixth', 'six', 'vi', 'emacs', '6', '6th'],
    ['seventh', 'seven', 'vii', '7', '7th'],
    ['eight', 'eighth', '8', 'viii', 'iix', '8th'],
    ['nine', 'nein', 'ninth', 'ix', '9', '9th'],
    ['ten', 'tenth', '10', '10th', 'x', 'by', 'times', 'product', 'multiplied', 'multiply'],
    ['eleventh', 'eleven', 'xi', '11th'],
    ['twelfth', 'twelveth', 'twelve', '12', 'xii', '12th'],
    ['thirteenth', 'thirteen', '13', 'xiii', '13th'],
    ['fourteenth', 'fourteen', 'ixv', '14th'],
    ['fifteenth', 'fifteen', '15', 'xv', '15th'],
    ['sixteenth', 'sixteen', '16', 'xvi', '16th'],
    ['seventeenth', 'seventeen', '17', 'xvii', '17th'],
    ['eighteenth', 'eighteen', 'eightteen', '18', 'xviii', '18th'],
    ['nineteenth', 'ninteenth', 'ninteen', 'nineteen', '19', 'ixx', '19th'],
    ['twentieth', 'twenty', 'xx', '20', '20th'],
    ['thirtieth', 'thirty', 'xxx', '30', '30th'],
    ['hundred', 'c', '100', '100th'],
    ['dr', 'doctor', 'drive'],
    ['mr', 'mister'],
    ['ms', 'miss', 'mrs'],
    ['st', 'saint', 'street'],
    ['rd', 'road'],
    ['albert', 'al'],
    ['robert', 'bob', 'rob'],
    ['william', 'will', 'bill'],
    ['richard', 'rich', 'dick'],
    ['jim', 'james'],
    ['gregory', 'greg'],
    ['christopher', 'chris'],
    ['benjamin', 'ben'],
    ['nicholas', 'nick'],
    ['anthony', 'tony'],
    ['lawrence', 'larry'],
    ['edward', 'edvard', 'edouard', 'ed'],
    ['kim', 'kimball'],
    ['vladimir', 'vlad'],
    ['vic','victor'],
    ['samuel', 'samantha', 'sam'],
    ['log', 'logarithm'],
    ['constant', 'number'],
]
equivalence_map = {}
for group in equivalence_list:
    for item in group:
        group_no_repeat = copy.deepcopy(group)
        group_no_repeat.remove(item)
        equivalence_map[item] = group_no_repeat

articles = ['a','an','the']

# known issue: if there are multiple words that have equivalents, will only get combinations for first word that's elgibile
def get_all_combinations(input_list):
    all_lists = [input_list]
    for word in input_list:
        if word in equivalence_map:
            for equivalent in equivalence_map[word]:
                copy_list = copy.deepcopy(input_list)
                copy_list[input_list.index(word)] = equivalent
                all_lists.append(copy_list)
    all_combinations = []
    for all_input_list in all_lists:
        combo = []
        for r in range(len(all_input_list) + 1):
            for combination in combinations(all_input_list, r):
                combo.append(''.join(text for text in list(combination)))
        del combo[0]
        for i in combo:
            if i not in all_combinations:
                all_combinations.append(i)
    return all_combinations

def process_string(text):
    text = ''.join([char for char in text if char.isalnum() or char == ' '])
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text_list = text.split(' ')
    text_list = [word for word in text_list if word not in articles]
    return text_list

def max_levenshtein(answer_options, guess):
    max_levenshtein_ratio = 0.0
    for option in answer_options:
        max_levenshtein_ratio = max(max_levenshtein_ratio, Levenshtein.ratio(option, guess))
    return max_levenshtein_ratio 

def check_answer(guess):
    global answer
    working_answer = get_all_combinations(process_string(answer))
    working_guess = ''.join([word for word in process_string(guess)])
    # magic number 0.9 for :
    return max_levenshtein(working_answer, working_guess) >= 0.9

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
    text = '**' + category + '** for $' + value + '\n\n'
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
    text = 'Answer: **' + answer + '**'
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
    
    ## Easter egg
    if message.content.startswith('!anderspestididwhat'):
        await message.channel.send('Anders Pesti slimed out Alex Baker on March 13, 2025.')
        return

    ## Display scores at any moment
    if message.content.startswith('!score'):
        if scores:
            text = '**Scores** \n\n'
            for player in scores:
                text = text + player + ': ' + str(scores[player]) + '\n'
            await message.channel.send(text)   
        else:
            await message.channel.send('No scores at the moment.')
        return 

    ## Display all commands at any moment 
    if message.content.startswith('!help'):
        text = '**All Commands**  \n\n'
        text += '\'!help\'    - Displays all commands. \n'
        text += '\'!play\'    - Starts the game. \n'
        text += '\'!stop\'    - Stops the game. \n'
        text += '\'!scorew\'  - Displays the current scores. \n'
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
                else:
                    if account not in scores:
                        scores[account] = 0 - int(value)
                    else:
                        scores[account] -= int(value)
        return
    
    if state == State.Stopped:
        if message.content.startswith('!play'):
            channel = message.channel
            state = State.Playing
            clue_loop.start()
            return

client.run(TOKEN)
