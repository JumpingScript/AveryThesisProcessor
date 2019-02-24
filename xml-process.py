#!/usr/bin/env python3
# A processor to read XML data for Avery's corpus.

import argparse
import os.path
from os import walk, getcwd, makedirs
import xml.etree.ElementTree as ET

# Import custom class.
import speaker

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
                dataLine = str(element)
            else:
                dataLine += "," + str(element)
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

def countPairs(data, age):
    """Counts how many of a single pair is in a given list.  Returns a tuple of age, pair, and count."""
    setData = list(set(data[:]))

    result = []

    for item in setData:
        count = data.count(item)
        result.append((age, item[0].word, item[1].word, count))

    return result

def countAdjectives(data, age):
    """Counts the number of adjectives for a particular age and returns a formatted CSV tuple."""
    setData = list(set(data[:]))

    result = []

    for item in setData:
        count = data.count(item)
        result.append((age, item.word, count))

    return result

def ageKey(val):
    """Simple function to allow sorting by the age of a speaker."""
    return val.age.decimal

def parseSpeakers(data):
    """Parse through the participant data, it accepts XML object data to parse through."""
    result = []

    role = None
    name = None
    sex = None
    age = None
    lang = None

    for part in data:
        # Gather every participant in turn.
        if urlScrub(part.tag) == "participant":
            sid = part.attrib['id']

            # Gather the actual data.
            for partData in part:
                if urlScrub(partData.tag) == "role":
                    role = partData.text
                elif urlScrub(partData.tag) == "name":
                    name = partData.text
                elif urlScrub(partData.tag) == "sex":
                    sex = partData.text
                elif urlScrub(partData.tag) == "age":
                    age = partData.text
                elif urlScrub(partData.tag) == "language":
                    lang = partData.text

            # A flag to see if this participant should be aborted.
            # Some data in the XML does not have all the requires information, this will abort adding
            # a speaker to the data set if the required data is not present.
            abort = False

            # Speaker data is stored as attributes of the XML Participant tags, the above will fail.
            if role is None and\
                    name is None and\
                    sex is None and\
                    age is None and\
                    lang is None:
                if "role" in part.attrib.keys():
                    role = part.attrib['role']
                if "name" in part.attrib.keys():
                    name = part.attrib['name']
                if "language" in part.attrib.keys():
                    lang = part.attrib['language']
                if "age" in part.attrib.keys():
                    age = part.attrib['age']
                if "sex" in part.attrib.keys():
                    sex = part.attrib['sex']

            if role is None or\
                    name is None or\
                    sex is None or\
                    age is None:
                abort = True

            # Build the speaker object.
            if not abort:
                curPart = speaker.Speaker(sid, role, name, sex, age, lang)
                result.append(curPart)

            # Set all values back to None before the next loop.
            role = None
            name = None
            sex = None
            age = None
            lang = None

    return result

def parseTranscript(data, speakers):
    """Parses through an XML data block for transcript information, updates list in-place."""
    s = None

    # Handle the format of transcript data which is stored under the u tag.
    if urlScrub(data.tag) == "u":
        sid = data.attrib['who']

        # Now find the speaker by the ID in the list.
        for part in speakers:
            if part.sid == sid:
                # When the speaker ID is found, make a reference to it.
                s = part
                break

        # Record if a noun is seen before an adjective.
        seenNoun = False
        seenAdj = False
        noun = None
        adj = None

        for w in data:
            # Look into the w tag for word data.
            if urlScrub(w.tag) == "w" and not s is None:
                # The word itself is stored in the w tag's text.
                word = speaker.Word(w.text)

                # This format does not store syntax information in the word text
                # so we will have to fill it in from tags within the word tax.
                for mor in w:
                    if urlScrub(mor.tag) == "mor":
                        for mw in mor:
                            if urlScrub(mw.tag) == "mw":
                                for pos in mw:
                                    if urlScrub(pos.tag) == "pos":
                                        for c in pos:
                                            # Parts of speech data is stored in this tag.
                                            if urlScrub(c.tag) == "c" and not word.word is None:
                                                if c.text == "n":
                                                    word.noun = True
                                                    seenNoun = True
                                                    noun = word
                                                elif c.text == "adj":
                                                    word.adj = True
                                                    seenAdj = True
                                                    adj = word
                                                    if seenNoun and not seenAdj:
                                                        word.beforeNoun = False
                                                    elif not seenNoun and seenAdj:
                                                        word.beforeNoun = True

                                                # Store the noun pairs in their appropriate list.
                                                if seenNoun and seenAdj:
                                                    if adj.beforeNoun:
                                                        s.prePairs.append((adj, noun))
                                                    else:
                                                        s.postPairs.append((adj, noun))
                                                    # Reset the flags so we don't add multiple pairs.
                                                    seenNoun = False
                                                    seenAdj = False

                                                # Store the word into the list for this speaker.
                                                if not word.punctuation:
                                                    s.words.append(word)
                    elif urlScrub(mor.tag) == "shortening":
                        word.word = word.word + mor.text
                        if not mor.tail is None:
                            if not mor.tail.strip() == "\n":
                                word.word = word.word + mor.tail

            # Look for adjectives without nouns (these are not used in statistics).
            if seenAdj and not seenNoun and not s is None and not adj.word is None:
                adj.orphan = True
                s.orphans.append(adj)

    # Handle the format of transcript data in groupTier/Morphology.
    else:
        for u in data:
            # Gather the speaker from the <u> tag.
            if urlScrub(u.tag) == "u":
                sid = u.attrib['speaker']

                # Now find the speaker by the ID in the list.
                for part in speakers:
                    if part.sid == sid:
                        # When the speaker ID is found, make a reference to it.
                        s = part
                        break

                # Now process the text via the groupTier tag under Morphology attribute.
                for g in u:
                    # Process the groupTier format.
                    if urlScrub(g.tag) == "grouptier" and not s is None:
                        # Look for the Morphology attribute.
                        if g.attrib['tierName'] == "Morphology":
                            # Record if a noun is seen before an adjective.
                            seenNoun = False
                            seenAdj = False
                            noun = None
                            adj = None

                            # Each word is stored in a <tg> tag and under that a <w> tag.
                            for t in g:
                                if urlScrub(t.tag) == "tg":
                                    for w in t:
                                        if urlScrub(w.tag) == "w":
                                            if not (w.text[0] == "("
                                                    or w.text[-1] == ")"
                                                    or w.text.find('|') < 0):
                                                word = speaker.Word(w.text)
                                                if word.noun:
                                                    seenNoun = True
                                                    noun = word
                                                elif word.adj:
                                                    seenAdj = True
                                                    word.adj = True
                                                    adj = word
                                                    if seenNoun and not seenAdj:
                                                        word.beforeNoun = False
                                                    elif not seenNoun and seenAdj:
                                                        word.beforeNoun = True

                                                # Store the noun pairs in their appropriate list.
                                                if seenNoun and seenAdj:
                                                    if adj.beforeNoun:
                                                        s.prePairs.append((adj, noun))
                                                    else:
                                                        s.postPairs.append((adj, noun))
                                                    # Reset the flags so we don't add multiple pairs.
                                                    seenNoun = False
                                                    seenAdj = False

                                                # Store the word into the list for this speaker.
                                                if not word.punctuation:
                                                    s.words.append(word)

                            # Look for adjectives without nouns (these are not used in statistics).
                            if seenAdj and not seenNoun:
                                adj.orphan = True
                                s.orphans.append(adj)

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

    # Variable to store all of the speaker data for all processed participants.
    allParts = []

    # Process all the XML files in the list.
    for file in fileList:
        print("Processing file '" + file + "'...")

        corpusTree = ET.parse(file)
        corpusRoot = corpusTree.getroot()

        # Stores the list of participants unique to this file.
        fileParts = []

        # Process from the root down.
        for chld in corpusRoot:
            # Process the Participants
            if urlScrub(chld.tag) == "participants":
                fileParts.extend(parseSpeakers(chld))
            # Process the actual word data, starting with the speaker.
            elif urlScrub(chld.tag) == "transcript":
                parseTranscript(chld, fileParts)
            # Process the other format of transcript data.
            elif urlScrub(chld.tag) == "u":
                parseTranscript(chld, fileParts)
            # Process the CHAT tag to descend further into the tree.
            elif urlScrub(chld.tag) == "chat":
                # In this case, all the data is under the tag of CHAT, so must drop into that tree.
                for c in chld:
                    # Process the Participants
                    if urlScrub(c.tag) == "participants":
                        fileParts.extend(parseSpeakers(c))
                    # Process the actual word data, starting with the speaker.
                    elif urlScrub(c.tag) == "transcript":
                        parseTranscript(c, fileParts)
                    # Process the other format of transcript data.
                    elif urlScrub(c.tag) == "u":
                        parseTranscript(c, fileParts)

        # Add all participants from this file to the master list.
        allParts.extend(fileParts)

    if len(allParts) < 1:
        print("There was an error processing the data, no participants were found.  Did you forget to specify '-r'?")
        return 1

    # A pair of lists to store all the statistical information before output to CSV files.
    childStats = []
    adultStats = []
    siblingStats = []

    # Gather statistics for each category of person.
    for spk in allParts:
        tmp = spk.getStats()
        if tmp[6] > 0:
            if spk.adult:
                adultStats.append(tmp)
            elif spk.sibling:
                siblingStats.append(tmp)
            else:
                childStats.append(tmp)

    # Going to copy the list as memory isn't an issue and I'd rather leave the original list intact.
    ageList = allParts[:]
    ageList.sort(key=ageKey)

    # A list to store all of the age / pair data for each group of 6 months and broken down by gender.
    prePairsM = []
    postPairsM = []
    prePairsF = []
    postPairsF = []

    # A list of adjectives that counts adjectives without pairs.
    preAdjM = []
    postAdjM = []
    preAdjF = []
    postAdjF = []

    # Now lets construct the CSV data from the sorted speaker list.
    maxAge = ageList[len(ageList) - 1].age.decimal
    ageLow = 0
    ageHigh = 0.5

    while ageHigh <= maxAge:
        # A list to store word pair data, each will be stored with a line for every 6 months.
        curGroupPreM = []
        curGroupPostM = []
        curGroupPreF = []
        curGroupPostF = []
        curGroupPostAdjM = []
        curGroupPostAdjF = []
        curGroupPreAdjM = []
        curGroupPreAdjF = []

        for spk in ageList:
            # Check ages and construct some lists.
            if ageLow < spk.age.decimal <= ageHigh:
                tmpAdj = spk.getAdjectives()

                if spk.sex == "male":
                    curGroupPreM.extend(spk.prePairs)
                    curGroupPostM.extend(spk.postPairs)
                    curGroupPreAdjM.extend(tmpAdj[0])
                    curGroupPostAdjM.extend(tmpAdj[1])
                if spk.sex == "female":
                    curGroupPreF.extend(spk.prePairs)
                    curGroupPostF.extend(spk.postPairs)
                    curGroupPreAdjF.extend(tmpAdj[0])
                    curGroupPostAdjF.extend(tmpAdj[1])

        # Construct the list of lists, including age data.
        if len(curGroupPreM) > 0:
            prePairsM.extend(countPairs(curGroupPreM, ageLow))
            preAdjM.extend(countAdjectives(curGroupPreAdjM, ageLow))

        if len(curGroupPostM) > 0:
            postPairsM.extend(countPairs(curGroupPostM, ageLow))
            postAdjM.extend(countAdjectives(curGroupPreAdjM, ageLow))

        if len(curGroupPreF) > 0:
            prePairsF.extend(countPairs(curGroupPreF, ageLow))
            preAdjF.extend(countAdjectives(curGroupPreAdjF, ageLow))

        if len(curGroupPostF) > 0:
            postPairsF.extend(countPairs(curGroupPostF, ageLow))
            postAdjF.extend(countAdjectives(curGroupPreAdjF, ageLow))

        ageLow = ageHigh
        ageHigh = ageHigh + 0.5

    # Construct the actual CSV files.
    statHeader = "Role,Name,Gender,Age (Dec),Age (Y;M),Words,Adjectives,Prenominal,% Prenominal"
    childCSV = genCSV(statHeader, childStats)
    adultCSV = genCSV(statHeader, adultStats)
    siblingCSV = genCSV(statHeader, siblingStats)

    adjheader = "Age Lower,Adjective,Noun,Count"
    adjPreMCSV = genCSV(adjheader, prePairsM)
    adjPostMCSV = genCSV(adjheader, postPairsM)
    adjPreFCSV = genCSV(adjheader, prePairsF)
    adjPostFCSV = genCSV(adjheader, postPairsF)

    adjheader2 = "Age Lower, Adjective, Count"
    adjCountPreMCSV = genCSV(adjheader2, preAdjM)
    adjCountPostMCSV = genCSV(adjheader2, postAdjM)
    adjCountPreFCSV = genCSV(adjheader2, preAdjF)
    adjCountPostFCSV = genCSV(adjheader2, postAdjF)

    # Create the output directory if needed.
    if not os.path.isdir(arg.output) and not arg.test:
        makedirs(arg.output)

    # Write the CSV files for per-speaker stats.
    writeCSV(childCSV, os.path.join(arg.output, "child.csv"), arg.test)
    writeCSV(adultCSV, os.path.join(arg.output, "adult.csv"), arg.test)
    writeCSV(siblingCSV, os.path.join(arg.output, "sibling.csv"), arg.test)

    # Write the gender-specific CSV files for adjective pair stats.
    writeCSV(adjPreMCSV, os.path.join(arg.output, "pre-adjective-pairs-male.csv"), arg.test)
    writeCSV(adjPostMCSV, os.path.join(arg.output, "post-adjective-pairs-male.csv"), arg.test)
    writeCSV(adjPreFCSV, os.path.join(arg.output, "pre-adjective-pairs-female.csv"), arg.test)
    writeCSV(adjPostFCSV, os.path.join(arg.output, "post-adjective-pairs-female.csv"), arg.test)

    # Write the gender-specific CSV files for the adjective counts.
    writeCSV(adjCountPreMCSV, os.path.join(arg.output, "pre-adjective-male.csv"), arg.test)
    writeCSV(adjCountPostMCSV, os.path.join(arg.output, "post-adjective-male.csv"), arg.test)
    writeCSV(adjCountPreFCSV, os.path.join(arg.output, "pre-adjective-female.csv"), arg.test)
    writeCSV(adjCountPostFCSV, os.path.join(arg.output, "post-adjective-female.csv"), arg.test)

    return 0

main()