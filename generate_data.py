"""
Generate the data for the game, based on jlpt_words.csv
"""
import csv
import gzip
import re
from collections import defaultdict
from itertools import combinations, product


def is_only_kanji(word):
    for char in word:
        if not (0x4e00 <= ord(char) <= 0x9faf):
            return False
    return True


def is_two_kanji_word(word):
    return len(word) == 2 and is_only_kanji(word)


word_to_lvl = {}
word_to_info = {}
nth_kanji_to_word = {0: defaultdict(set), 1: defaultdict(set)}
kanjis = set()
with gzip.open("jlpt_words.csv.gz", "rt") as f:
    reader = csv.reader(f)
    for tokens in reader:
        # Get word in kanji
        word = tokens[0]
        # Clean up annotations that may appear after the word
        word = re.sub(r"\(.*\)", "", word).strip()
        # Filter two kanji words
        if not is_two_kanji_word(word):
            continue
        # Get the JLPT level
        tags = set(tokens[-1].split(" "))
        for lvl in range(1, 6):
            if f"JLPT_{lvl}" in tags or f"JLPT_N{lvl}" in tags:
                word_to_lvl[word] = lvl

        word_to_info[word] = (tokens[1], tokens[2])
        for n in range(2):
            nth_kanji_to_word[n][word[n]].add(word)
            kanjis.add(word[n])

# For each kanji, find all puzzles!
valid_words = set()
with gzip.open("puzzles.csv.gz", "wt") as f:
    writer = csv.writer(f, delimiter=',')
    for kanji in kanjis:
        no_candidates = False
        matches = {}
        for n in range(2):
            matches[n] = nth_kanji_to_word[n][kanji]
            if len(matches[n]) < 2:
                no_candidates = True
                break
        if no_candidates:
            continue
        print(f'kanji: {kanji} matches: {matches}')
        for end_words, start_words in product(combinations(matches[0], 2), combinations(matches[1], 2)):
            # Level is based on the "hardest" word
            lvl = min(word_to_lvl[w] for w in start_words + end_words)
            print(f"{start_words} -> {end_words} (N{lvl})")
            writer.writerow([kanji, start_words[0][0], start_words[1][0], end_words[0][1], end_words[1][1], lvl])
        valid_words.update(matches[0], matches[1])

print("# Valid words: ", len(valid_words))

# Write the details for all words that have some puzzle
with gzip.open("words_info.csv.gz", "wt") as f:
    writer = csv.writer(f, delimiter=',')
    for word in valid_words:
        writer.writerow([word, *word_to_info[word]])
