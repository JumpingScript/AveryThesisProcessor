#!/usr/bin/env python3
# A processor to read XML data for Avery's corpus.

import argparse
import os.path
from os import walk, getcwd, makedirs
import xml.etree.ElementTree as ET

# Import custom classes.
import speaker
import sentence

def urlScrub(data):
    """Scrubs URL data from a line of XML text, the URL is encased in {}"""
    # This function also puts the result into all lowercase, to make pattern matching easier.
    result = data.split("}")[1]
    return result.lower()

def findXML(directory, r = False):
    """Takes a directory specification and produces a list of XML files."""
    result = []

    for (dirpath, dirnames, filenames) in walk(directory):
        for file in filenames:
            if file[-3:].lower() == "xml":
                result.append(os.path.join(dirpath, file))

        if not r:
            dirnames.clear()

    return result

def genCSV(hdr, data):
    """Generate a list of CSV formatted strings from a list of statistical data."""
    result = [hdr]

    # Add data to file.
    for item in data:
        dataLine = ""
        for element in item:
            if len(dataLine) == 0:
                if type(element) == str:
                    dataLine = element
                else:
                    dataLine = "=" + str(element)
            else:
                if type(element) == str:
                    dataLine += "," + element
                else:
                    dataLine += ",=" + str(element)
        result.append(dataLine)

    return result

def writeCSV(data, file, test = False):
    """Write CSV formatted data to a file."""
    if len(data) > 1:
        if test:
            for line in data:
                print(line)
        else:
            print("Saving CSV data to '" + file + "'.")
            f = open(file, "w")

            for line in data:
                print(line, file=f)

            f.close()
    else:
        print("No data found for '" + file + "', skipping.")

def ageKey(val):
    """Simple function to allow sorting by the age of a speaker."""
    return val.age.decimal

def corpusPB12(dataXML):
    """Processes Corpus Data for version PB1.2 such as the Lyon Corpus.
    Accepts input of XML data for processing and returns a list of Sentence objects.
    """
    result = [] # This will eventually store the completed list of Sentence objects.
    speakers = []

    for child in dataXML:
        # Process participants to get participant IDs and build speakers.
        if urlScrub(child.tag) == 'participants':
            for part in child:
                if urlScrub(part) == 'participant':
                    sID = part.attibute['id']
                    sRole = None
                    sName = None
                    sSex = None
                    sAge = None
                    sLang = None
                    for partData in part:
                        if urlScrub(partData) == 'role':
                            sRole = partData.text
                        elif urlScrub(partData) == 'name':
                            sName = partData.text
                        elif urlScrub(partData) == 'sex':
                            sSex = partData.text
                        elif urlScrub(partData) == 'age':
                            sAge = partData.text
                        elif urlScrub(partData) == 'language':
                            sLang = partData.text
                    speakers.append(speaker.Speaker(sID, sRole, sName, sSex, sAge, sLang))
        # Now for the actual transcript data.  Before this tag is reached we assume
        # that we will actually have all the speakers for this file.
        elif urlScrub(child.tag) == 'transcript':
            for u in child:
                if urlScrub(u.tag) == 'u':
                    sentenceText = "" # Full reconstructed sentence
                    thisSpeaker = None # Where to put the speaker data
                    sID = u.attribute['speaker']
                    # We need to locate this speaker in the list.
                    for s in speakers:
                        if s.sid == sID:
                            thisSpeaker = s
                        else:
                            raise ValueError('Speaker not found in data.')
                    # We have located the speaker, now we can process the actual text.
                    for ortho in u:
                        if urlScrub(ortho.tag) == 'orthography':
                            for g in ortho:
                                if urlScrub(g.tag) == 'g':
                                    for w in g:
                                        if urlScrub(w.tag) == 'w': # Words
                                            if not w.text == "": # Ignore empty text.
                                                sentenceText += " "
                                                sentenceText += w.text
                                        elif urlScrub(w.tag) == 'p': # Punctuation
                                            if not w.text == "": # Ignore empty text.
                                                sentenceText += w.text

                    # Check to make sure it is logical to append the data.
                    if not (sentenceText == "" or thisSpeaker is None):
                        result.append(sentence.Sentence(thisSpeaker, sentenceText))

    return result

def corpus271(dataXML):
    """Processes Corpus Data for version 2.7.1 such as Palasis and MTLM.
    Accepts input of XML data for processing and returns a list of Sentence objects.
    """
    result = []

    return result

def main():
    # Argument parsing.
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, help="The name of the XML file to be processed.")
    parser.add_argument("-d", "--dir", type=str, help="The directory name to find XML files to processed.")
    parser.add_argument("-o", "--output", type=str, help="The directory to output CSV files to.",
                        default=getcwd())
    parser.add_argument("-r", "--recursive", help="Should a directory be looked at recursively.", action='store_true')
    parser.add_argument("-t", "--test", help="Test mode, output goes to console.", action='store_true')

    arg = parser.parse_args()

    # Validate that the user gave the program something to do.
    if arg.file is None and arg.dir is None:
        print("You must specify either a file or directory to process, use '-h' for help.")
        return 1

    # Initialize a place to put the file list to process.
    fileList = []

    # Process any file and directory names and make a list to iterate through.
    if not arg.file is None:
        if not os.path.isfile(arg.file):
            print("File " + arg.file + " not found or is not a file.")
            return 1
        fileList.append(arg.file)
    elif not arg.dir is None:
        if not os.path.isdir(arg.dir):
            print("Directory " + arg.dir + " not found or is not a directory.")
            return 1
        fileList = findXML(arg.dir, arg.recursive)

    # Process all the XML files in the list.
    for file in fileList:
        print("Processing file '" + file + "'...")

        corpusTree = ET.parse(file)
        corpusRoot = corpusTree.getroot()

        # Need to determine file version for processing, since different files have
        # different capitalization, we need to account for that.
        if 'version' in corpusRoot.attrib:
            ver = corpusRoot.attrib['version']
        elif 'Version' in corpusRoot.attrib:
            ver = corpusRoot.attrib['Version']
        else:
            ver = ""

        # Now branch to the proper processor.
        if ver == 'PB1.2':
            data = corpusPB12(corpusRoot)
        elif ver == '2.7.1':
            data = corpus271(corpusRoot)

    return 0

main()