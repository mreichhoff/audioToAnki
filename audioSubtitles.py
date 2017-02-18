#!/usr/bin/env python3
import re
from pydub import AudioSegment
import argparse
import os
import xml.etree.ElementTree as ET

#anki import uses ; for question/answer separator, so replace ; with ...
def extractAnswers(filename):
    fileExtension = os.path.splitext(filename)[1]
    output = []
    if(fileExtension == ".txt"):
        lines = readInput(filename)
        for line in lines:
            output.append(extractAnswer(line))
    elif(fileExtension == ".xml"):
        timedText = ET.ElementTree().parse(filename)
        output = [x.text.replace(";", "...") for x in timedText[0].findall("p")]
    elif(fileExtension == ".vtt"):
        output = []
        currentAnswer = ""
        collectLines = False
        lines = readInput(filename)
        for line in lines:
            if("-->" in line):
                collectLines = True
            elif(collectLines and (not line.strip())):
                output.append(currentAnswer.replace(";", "...").strip())
                currentAnswer = ""
                collectLines = False
            elif(collectLines):
                currentAnswer += " " + line
        if(currentAnswer):
            output.append(currentAnswer.replace(";", "...").strip())
    return output

def extractAnswer(line):
    inputs = line.split(':')
    if(len(inputs) == 2):
        return inputs[1].replace(";", "...")
    return "error"

#TODO handle this txt vs xml stuff more cleanly
def extractTimings(filename):
    fileExtension = os.path.splitext(filename)[1]
    output = []
    if(fileExtension == ".txt"):
        #TODO list comprehension here
        #TODO readInput is done twice and involves file IO...fix
        lines = readInput(filename)
        for line in lines:
            output.append(extractTiming(line))
    elif(fileExtension == ".xml"):
        #handle timed text format (as seen on youtube)
        timedText = ET.ElementTree().parse(filename)
        output = [(int(x.attrib['t']), int(x.attrib['t'])+ int(x.attrib['d'])) for x in timedText[0].findall("p")]
    elif(fileExtension == ".vtt"):
        lines = readInput(filename)
        timestamps = [line for line in lines if "-->" in line]
        output = [convertTimestamp(timestamp) for timestamp in timestamps]
    return output

def convertTimestamp(timestamp):
    components = timestamp.split("-->")
    start = components[0].strip()
    #per https://w3c.github.io/webvtt/, there can be formatting info at the end of a webvtt timestamp (e.g., 00:00:03.639 line:74%), which explains this nastiness
    end = components[1].strip().split(" ")[0]

    #give a 1 sec buffer on either side since subtitle timings can be inconsistent...ugh
    startMilliseconds = convertVttTimeToMilliseconds(start)- 1000
    if(startMilliseconds < 0):
        startMilliseconds = 0
    endMilliseconds = convertVttTimeToMilliseconds(end)+ 1000
    return (startMilliseconds, endMilliseconds)

def convertVttTimeToMilliseconds(timestamp):
    timestampComponents = re.search('(\d\d):(\d\d):(\d\d).(\d\d\d)', timestamp)
    total = 0
    #vtt timestamps can have minutes or hours be the most significant component...see w3c github link above
    if(timestampComponents == None):
        timestampComponents = re.search('(\d\d):(\d\d).(\d\d\d)', timestamp)
        total = (int(timestampComponents.groups()[0])*60*1000) + (int(timestampComponents.groups()[1])*1000) + (int(timestampComponents.groups()[2]))
    else:
        total = (int(timestampComponents.groups()[0])*60*60*1000) + (int(timestampComponents.groups()[1])*60*1000) + (int(timestampComponents.groups()[2])*1000) + (int(timestampComponents.groups()[3]))

    return total

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

#TODO: audio file type independence
audio = AudioSegment.from_file(args.audioFilename, "mp3")
timings = extractTimings(args.subtitlesFilename)
answers = extractAnswers(args.subtitlesFilename)

for timing in timings:
    clip = audio[timing[0]:timing[1]]

    #TODO pass this in as an arg instead of hardcoding...make filename stuff less ugly
    out_f = open("/Users/mreichhoff/Library/Application Support/Anki2/User 1/collection.media/" + os.path.split(args.audioFilename)[1].replace(" ", "").replace(".mp3","")+str(timing[0]) + str(timing[1])  + ".mp3", 'wb')
    clip.export(out_f, format='mp3')

for index, answer in enumerate(answers):
    print("[sound:" + os.path.split(args.audioFilename)[1].replace(" ", "").replace(".mp3", "")+str(timings[index][0]) + str(timings[index][1])  + ".mp3]" + ";" + answers[index])
