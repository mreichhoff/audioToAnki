#!/usr/bin/env python3
import re
from pydub import AudioSegment
import argparse
import os

def extractAnswers(lines):
    output = []
    for line in lines:
        output.append(extractAnswer(line))
    return output

def extractAnswer(line):
    inputs = line.split(':')
    if(len(inputs) == 2):
        return inputs[1]
    return "error"

def extractTimings(lines):
    output = []
    #TODO list comprehension here
    for line in lines:
        output.append(extractTiming(line))
    return output

def extractTiming(line):
    inputs = line.split(':')
    #ignoring bad input for now
    if(len(inputs) == 2):
        timing = inputs[0]
        timingStartEnd = timing.split('-')
        #ignoring bad input for now
        if(len(timingStartEnd) == 2):
            timingStart = timingStartEnd[0]
            timingEnd = timingStartEnd[1]

            timingStartMilliseconds = convertTimeToMilliseconds(timingStart)
            timingEndMilliseconds = convertTimeToMilliseconds(timingEnd)

            return (timingStartMilliseconds, timingEndMilliseconds)
    return (0, 0)

#given timestamp like 1h3m2s, return the corresponding number of milliseconds
def convertTimeToMilliseconds(timestamp):
    segments = re.findall("[0-9]+[hms]", timestamp)
    total = 0
    for segment in segments:
        #TODO enums and input checking
        if('h' in segment):
            total += 60*60*1000*getNumericPortion(segment)
        elif('m' in segment):
            total += 60*1000*getNumericPortion(segment)
        elif('s' in segment):
            total += 1000*getNumericPortion(segment)
    return total

#TODO make less ugly
def getNumericPortion(segment):
    return int(segment[:len(segment)-1])

def readInput(subtitlesFilename):
    with open(subtitlesFilename) as subtitlesFile:
        timeToTextMappings = [line.rstrip('\n') for line in subtitlesFile.readlines()]
        return timeToTextMappings

#TODO input validation, edge cases, etc.
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("audioFilename", help="")
parser.add_argument("subtitlesFilename", help="")
args = parser.parse_args()

audio = AudioSegment.from_file(args.audioFilename, "mp3")
lines = readInput(args.subtitlesFilename)

timings = extractTimings(lines)
answers = extractAnswers(lines)

for timing in timings:
    clip = audio[timing[0]:timing[1]]

    #TODO pass this in as an arg instead of hardcoding
    out_f = open("/Users/mreichhoff/Library/Application Support/Anki2/User 1/collection.media/" + os.path.split(args.audioFilename)[1].replace(" ", "").replace(".mp3","")+str(timing[0]) + str(timing[1])  + ".mp3", 'wb')
    clip.export(out_f, format='mp3')

for index,answer in enumerate(answers):
    print("[sound:" + os.path.split(args.audioFilename)[1].replace(" ", "").replace(".mp3","")+str(timings[index][0]) + str(timings[index][1])  + ".mp3]" + ";" + answers[index])
        
