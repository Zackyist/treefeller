# Treefeller, a Hangman solver for Gofore's programming challenge
# 22.3.2017
# http://github.com/zackyist/

# Requires Python 3
# Uses the FuzzyWuzzy package for fuzzy string matching:
#   https://github.com/seatgeek/fuzzywuzzy

import re
import sys
from fuzzywuzzy import process

def main(agrv):
    # Begin by printing the player (solver) name
    print("Treefeller")

    # Capture and store the hangman dictionary provided line-by-line as a list
    allWords = []
    readWord = input()
    while (readWord != ""):
        allWords.append(readWord)
        readWord = input()

    # Mark this guess as the first guess and initialise the current hangman
    # dictionary as well as the list of banned characters
    firstGuess = True
    words = allWords
    bannedChars = []

    while(True):
      # Capture and parse the status line until EOF
      try:
        status = input()
      except EOFError:
        break
      status = status.split()
      guessed = False
      guessedWord = ""

      # If the status is WIN or LOSE, reinitialise and restart the loop. Otherwise
      # evaluate the unfinished word
      if (status[0] == "WIN") or (status[0] == "LOSE"):
        firstGuess = True
        words = allWords
        bannedChars = []
        continue
      unfinishedWord = status[0]

      # If this is the first guess, trim the current dictionary to only contain
      # words of exactly the target length. Also calculate the most frequent
      # characters in the dictionary
      if firstGuess == True:
        targetLength = len(unfinishedWord)
        words = trimWordsByLength(words, targetLength)
        mostFrequentChars = calculateDictionaryFrequencies(words)
        firstGuess = False

        # If there is only one entry left in the dictionary after trimming,
        # guess that entry
        if len(words) == 1:
          guessedWord = words[0]
          print(guessedWord)
          guessed = True

      # Do a fuzzy string comparison between the unfinished word and all the
      # words in the current dictionary. Update the dictionary to contain only
      # the words that match over 0% (unless this is the first guess, in which
      # case none match)
      if guessed == False:
        words = optimiseWords(words, unfinishedWord)
        fuzzyMatches = process.extract(unfinishedWord, words)

      # If there is only one fuzzy match, guess it
      if (len(fuzzyMatches) == 1) and (guessed == False):
        guessedWord = fuzzyMatches[0][0]
        print(guessedWord)
        guessed = True

      # If the first fuzzy match is over 60% and the second one is at least 20%
      # less likely, guess the first match
      if (len(fuzzyMatches) > 1) and (guessed == False):
        firstPercentage = fuzzyMatches[0][1]
        secondPercentage = fuzzyMatches[1][1]
        if (firstPercentage > 60) and (secondPercentage <= firstPercentage - 20):
          guessedWord = fuzzyMatches[0][0]
          print(guessedWord)
          guessed = True

      # Otherwise, calculate all the possible remaining characters from the
      # remaining possible words and guess the most frequent one. If there are
      # no correctly guessed characters yet, guess the most frequent letter in
      # the original dictionary
      if guessed == False:
        charFrequencies = calculateCharFrequency(words, unfinishedWord, bannedChars)

        if len(charFrequencies) != 0:
          print(charFrequencies[0])
          guessedChar = charFrequencies[0]
        else:
          mostFrequentChars = trimChars(mostFrequentChars, bannedChars)
          print(mostFrequentChars[0])
          guessedChar = mostFrequentChars[0]

      # Add the guessed character to banned characters no matter if it's a
      # hit or miss. Capture the result line and parse it. If the result was
      # a miss, trim the any words containing the guessed char from the
      # dictionary
      if guessed == False:
        bannedChars.append(guessedChar)

      result = input().split()
      if (result[0] == "MISS") and (guessed == False):
        words = trimWordsByGuessed(words, guessedChar)
      elif (result[0] == "MISS") and (guessed == True):
        words = trimGuessedWord(words, guessedWord)


# Returns a list of all possible letters ordered by their frequency in current
# possible words. Skips any banned characters
def calculateCharFrequency(words, unfinished, bannedChars):
    # If the unfinished word has a dot at some position, add the char at the
    # same position in each possible word to the possible chars dict. If the
    # char already exists in the dict, add to its frequency score
    unguessedIndices = []
    for idx, char in enumerate(unfinished):
        if char == '.':
            unguessedIndices.append(idx)

    possibleChars = {}
    if len(unguessedIndices) != len(unfinished):
      for word in words:
          for idx in unguessedIndices:
              char = word[idx]
              if char in bannedChars:
                continue
              if char in possibleChars:
                  possibleChars[char] += 1
              else:
                  possibleChars[char] = 1

    sortedChars = sorted(possibleChars, key=possibleChars.__getitem__)
    sortedChars = list(reversed(sortedChars))
    return sortedChars


# Returns a list of all the letters in the original hangman dictionary,
# ordered by their frequency
def calculateDictionaryFrequencies(words):
    # This part has been shamelessly stolen from Gofore's solver example
    letters = {letter for word in words for letter in word}
    frequencies = [(letter, sum(word.count(letter) for word in words)) for
    letter in letters]
    frequencies = sorted(frequencies, key=lambda a: a[1], reverse=True)

    sortedChars = []
    for letter, frequency in frequencies:
      sortedChars.append(letter)
    return sortedChars


# Creates a regex pattern string for the given word
def formRegexPattern(word):
    regex = "^"
    for char in word:
      if char == '.':
        regex += "[a-zåäö]"
      else:
        regex += char

    regex += "$"
    return regex


# Returns a boolean based on whether the given word matches the given regex
# pattern or not
def matchesRegex(word, regex):
    pattern = re.compile(regex)
    if pattern.match(word) != None:
      return True

    return False


# Returns an optimised word list based on regex
def optimiseWords(words, unfinished):
    regex = formRegexPattern(unfinished)
    regexList = []
    for word in words:
      if matchesRegex(word, regex):
        regexList.append(word)

    return regexList


# Returns a list of characters from which all banned characters have been
# removed
def trimChars(chars, bannedChars):
    newChars = chars
    for char in bannedChars:
      if char in newChars:
        newChars.remove(char)
    return newChars


# Removes the given guessed word from the word list
def trimGuessedWord(words, guessedWord):
    newList = words
    if guessedWord in words:
      newList.remove(guessedWord)
    return newList


# Returns the list of given words with all words containing the given character
# removed
def trimWordsByGuessed(words, char):
    newList = []
    for word in words:
      if char not in word:
        newList.append(word)

    return newList


# Returns a trimmed version of the words list. The trimmed list only contains
# words of the given length
def trimWordsByLength(words, length):
    newList = []
    for word in words:
        if len(word) == length:
            newList.append(word)

    return newList


if __name__ == "__main__":
    main(sys.argv)
