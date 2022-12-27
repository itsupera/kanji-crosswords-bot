Discord bot to play a Japanese crossword-like game with two kanji words.

For example:
```
Guess the mystery kanji (words from JLPT N3 or easier):
・・・・・
・　文　・
・数？引・
・　体　・
・・・・・
```

# Setup

## With Docker
```
docker build -t kanji-crosswords-bot .
docker run -e DISCORD_TOKEN="<your token>" \
    -e DISCORD_GUILD="<your discord guild>" \
    -e DISCORD_CHANNEL="<your channel name>" \
    kanji-crosswords-bot
```

## With Virtualenv

Install Python 3.9 and Virtualenv, then:
```
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
python3 generate.py
python3 bot.py
```