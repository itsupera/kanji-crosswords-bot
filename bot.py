import csv
import gzip
import os
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')


def load_level_to_kanji_to_words():
    level_to_kanji_to_words = {lvl: defaultdict(list) for lvl in range(1, 6)}
    with gzip.open('puzzles.csv.gz', 'rt') as f:
        reader = csv.reader(f)
        for kanji, start_words_0_0, start_words_1_0, end_words_0_1, end_words_1_1, lvl in reader:
            level_to_kanji_to_words[int(lvl)][kanji].append((start_words_0_0, start_words_1_0, end_words_0_1, end_words_1_1))
    return level_to_kanji_to_words


LEVEL_TO_KANJI_TO_WORDS = load_level_to_kanji_to_words()
LEVEL = 3
MAX_LEVEL = max((k for k,v in LEVEL_TO_KANJI_TO_WORDS.items() if len(v)))  # Highest level that has some puzzles
PUZZLE = None


@dataclass
class Puzzle:
    kanji: str
    start_words_0_0: str
    start_words_1_0: str
    end_words_0_1: str
    end_words_1_1: str
    lvl: int

    def __str__(self):
        return f'Guess the mystery kanji (words from JLPT N{self.lvl} or easier):\n' \
               f'・・・・・\n' \
               f'・　{self.start_words_0_0}　・\n' \
               f'・{self.start_words_1_0}？{self.end_words_0_1}・\n' \
               f'・　{self.end_words_1_1}　・\n' \
               f'・・・・・'

    def is_correct(self, content: str) -> bool:
        """ A correct answer is either mystery kanji or one of the words that make up the puzzle. """
        return content in {
            self.kanji,
            self.start_words_0_0 + self.kanji,
            self.start_words_1_0 + self.kanji,
            self.kanji + self.end_words_0_1,
            self.kanji + self.end_words_1_1
        }


def pick_puzzle():
    kanjis = list(LEVEL_TO_KANJI_TO_WORDS.get(LEVEL, {}).keys())
    if not kanjis:
        raise Exception(f'No kanji for level {LEVEL}')
    kanji = random.choice(kanjis)
    other_kanjis = random.choice(LEVEL_TO_KANJI_TO_WORDS[LEVEL][kanji])
    print(f'kanji: {kanji} other_kanjis: {other_kanjis} LEVEL: {LEVEL}')
    start_words_0_0, start_words_1_0, end_words_0_1, end_words_1_1 = other_kanjis
    return Puzzle(kanji, start_words_0_0, start_words_1_0, end_words_0_1, end_words_1_1, LEVEL)


class MyClient(discord.Client):
    prefix = '!'
    help_msg = f':person_tipping_hand: Available commands:\n' \
               f'- `{prefix}play` (or `{prefix}p`): start playing a new puzzle\n' \
               f'- `{prefix}giveup` (or `{prefix}g`): give up and see the answer\n' \
               f'- `{prefix}level <LEVEL>` (or `{prefix}l <LEVEL>`): change JLPT level (1-{MAX_LEVEL})\n' \
               f'- `{prefix}help`: show this message'

    async def on_ready(self):
        random.seed(time.time())

        for guild in self.guilds:
            if guild.name == GUILD:
                break

        print(
            f'{self.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})\n'
            f'Will interact on channel: {CHANNEL}\n'
        )

    async def on_message(self, message):
        global PUZZLE

        print(f"on_message (channel {message.channel.name}) : content={message.content} author={message.author} self.user={self.user}")

        # Ignore messages from self
        if message.author == self.user:
            return
        # Ignore messages from other channels
        if message.channel.name != CHANNEL:
            print(f"Not on our channel: '{message.channel.name}' != '{CHANNEL}'")
            return

        # Process commands
        if message.content.startswith(self.prefix):
            await self.process_command(message)
        elif PUZZLE and PUZZLE.is_correct(message.content):
            print(f"Correct!")
            PUZZLE = pick_puzzle()
            await message.channel.send(f'✅ Correct! The mystery kanji was `{PUZZLE.kanji}`!\nHere is a new one:\n\n{PUZZLE}')
        elif PUZZLE:
            await message.channel.send(f"❌ Wrong! The answer is NOT `{message.content}`")
        else:
            await message.channel.send(f'Use command `!p` to start a game')

    async def process_command(self, message):
        global PUZZLE, LEVEL

        if message.content[1:] in {'p', 'play'}:
            print(f"Let's play!")
            PUZZLE = pick_puzzle()
            await message.channel.send(PUZZLE)
        elif message.content[1:] in {'g', 'giveup'}:
            print(f"Give up!")
            answer = PUZZLE.kanji
            PUZZLE = pick_puzzle()
            await message.channel.send(f':sweat: Giving up? The mystery kanji was `{answer}`\nHere is a new one:\n\n{PUZZLE}')
            PUZZLE = None
        elif m := re.match(r'l(?:evel)? (\d)', message.content[1:]):
            try:
                new_level = int(m.group(1))
                if new_level not in range(1, MAX_LEVEL + 1):
                    raise ValueError()
            except ValueError:
                await message.channel.send(f'Invalid level: {m.group(1)}')
                return
            LEVEL = new_level
            PUZZLE = pick_puzzle()
            await message.channel.send(f':arrows_clockwise: Changing to JLPT N{LEVEL} level.\n\n{PUZZLE}')
        elif message.content[1:] in {'h', 'help'}:
            await message.channel.send(self.help_msg)
        else:
            await message.channel.send(f'Unknown command, use `!help` to get a list of commands')


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)