#! /usr/bin/env python
import os, sys, re, time
from os.path import isfile, isdir, join, dirname, splitext, exists, basename

def canonicalize(word):
    return removeNonAlphaNumerics(word).lower()

nonAlphaNumPat = re.compile(r'\W+')

def removeNonAlphaNumerics(string):
    return nonAlphaNumPat.sub('', string)

def removeUnwantedChars(badCharStr, string):
    return filter(lambda c: c not in badCharStr, string)

def filterSpaceTokens(tokens):
    '''remove that are only spaces or empty'''
    return [t for t in tokens if not (t == '' or t.isspace()) ]

def isSubjectTerm(token):
    tok = canonicalize(token)
    return tok in ['subject', 'title', 're', 'snbject']

def isDateTerm(token):
    tok = canonicalize(token)
    return tok in ['date', 'dated']


def findSubject(tokens):
    '''Returns the pair (index, subjectVal), where
    (1) index is the index of the first token of
    the first subject term found
    (2) subjectVal is the subject
    '''
    tokLen = len(tokens)
    for i in range(tokLen-1):
        if isSubjectTerm(tokens[i]):
            subjectVal =  ' '.join(tokens[i+1:])
            # remove date if present
            subjectTokens = subjectVal.split()
            idTuple = findDate(subjectTokens)
            if idTuple: # if date found
                index = idTuple[0]
                # return subject value without date term and date value tokens
                # the date is assumed to be 3 tokens
                return (i, ' '.join(subjectTokens[:index] + subjectTokens[index+4:]))
            else:
                return (i, subjectVal)

def getSubject(filepath):
    infile = open(filepath, 'r')
    lineIterator = infile.__iter__()
    for line in lineIterator:
        line = removeUnwantedChars(',', line)
        tokens = line.split()
        isTuple = findSubject(tokens)
        if isTuple: return isTuple[1]
        # If subject term is the last token,
        # return the next line if it exists
        if(tokens and isSubjectTerm(tokens[-1])):
            try: return lineIterator.next().strip()
            except StopIteration: return None
    infile.close()
    return None

dateFormats = ['%d %B %Y',   # 02 january 2008
               '%d %b %Y',   # 02 jan 2008
               '%d %m %Y',   # 02 01 2008
               
               '%d %B %y',   # 02 january 08
               '%d %b %y',   # 02 jan 08
               '%d %m %y',   # 02 01 08
               
               '%B %d %Y',   # january 02 2008
               '%b %d %Y',   # jan 02 2008
               '%m %d %Y',   # 01 02 2008
               
               '%B %d %y',   # january 02 08
               '%b %d %y',   # jan 02 08
               '%m %d %y',   # 01 02 08
               ]

puncAndSpacesPat = re.compile(r'[\W\s]+')

# Return the pair (firstIndex, length, dateObj), where
# 
def findDate(tokens):
    '''Returns the pair (index, dateObj), where
    (1) index is the index of the first token of
    the first date found
    (2) dateObj is the struct_time object representing the date found.
    If no such date is found, then None is returned
    '''
    # Further split by punctuation
    line = ' '.join(tokens)
    tokens = puncAndSpacesPat.split(line)
    tokLen = len(tokens)
    for i in range(tokLen-3):
        if isDateTerm(tokens[i]):
            # Check if next 3 tokens form a date
            dateStr = ' '.join(tokens[i+1:i+4])
            for fmt in dateFormats:
                try: return (i, time.strptime(dateStr, fmt))
                except ValueError: pass
    return None

def getDate(filepath):
    infile = open(filepath, 'r')
    for line in infile:
        # replace commas with spaces
        line = line.replace(',', ' ')
        tokens = line.split()
        idTuple = findDate(tokens)
        if idTuple: return idTuple[1]
    infile.close()
    return None


def isPrefixOf(list1, list2):
    '''returns True if list1 is a prefix of list2'''
    list1Len = len(list1)
    list2Len = len(list2)
    if list1Len > list2Len: return False
    return list1 == list2[:list1Len]
    

memoLists = [['memo', 'number'],
            ['memo', 'no'],
            ['memo', 'nnmber'],
            ]

def getMemoNum(filepath):
    infile = open(filepath, 'r')
    for line in infile:
        line = removeUnwantedChars(',', line)
        tokens = line.split()
        maxIndex = len(tokens)-1
        for i in range(maxIndex):
            # Determine if the next tokens
            # form a memo term
            canonTokens = map(canonicalize, tokens[i:])
            for mlist in memoLists:
                memoValIndex = i+len(mlist)
                if isPrefixOf(mlist, canonTokens) \
                  and memoValIndex <= maxIndex:
                    memoVal = tokens[memoValIndex]
                    # if memoVal contains a digit then
                    # it's a valid memo number
                    digitFound = False
                    for c in memoVal:
                        if c.isdigit(): digitFound = True
                    if digitFound: return memoVal
    infile.close()
    return None


def isToTerm(token):
    tok = canonicalize(token)
    return tok == 'to'

def getTo(filepath):
    infile = open(filepath, 'r')
    for line in infile:
        line = removeUnwantedChars(',', line)
        tokens = line.split()
        for i in range(len(tokens)-1):
            if isToTerm(tokens[i]):
                return getName(tokens[i+1:]) 
    infile.close()
    return None

def getName(tokens):
    numTokens = len(tokens)
#    print 'tokens:', tokens
    if numTokens > 2 and len(tokens[1]) == 2 and \
       tokens[1][1] == '.' and tokens[1][0].isalpha():
        return ' '.join(tokens[:3])
    else: return ' '.join(tokens[:2])
    

def isFromTerm(token):
    tok = canonicalize(token)
    return tok == 'from'


def getFrom(filepath):
    infile = open(filepath, 'r')
    for line in infile:
        line = removeUnwantedChars(',', line)
        tokens = line.split()
        for i in range(len(tokens)-1):
            if isFromTerm(tokens[i]):
                return getName(tokens[i+1:]) 
    infile.close()
    return None


def getInfoFromFile(filepath):
    subjectVal = getSubject(filepath)
    programVal = getProgram(subjectVal)
    return (subjectVal,
            getDate(filepath),
            getMemoNum(filepath),
            getTo(filepath),
            getFrom(filepath),
            programVal)

def getFilePaths(filepath):
    if isfile(filepath): return [filepath]
    elif isdir(filepath):
        l = [join(filepath, f) for f in os.listdir(filepath)]
        return filter(isfile, l)
    else:
        raise IOError, 'No such file or directory: ' + filepath

def getPdfPaths(filepath):
    return [f for f in getFilePaths(filepath)
                if splitext(f)[1].lower() == '.pdf' ]

txtprefix = 'TEXT'

def getTxtPaths(filepath):
    l = []
    for f in getFilePaths(filepath):
        filename = basename(f)
        if filename.startswith(txtprefix) and \
          splitext(filename)[1].lower() == '.txt':
            l.append(f)
    return l

def pdfPath2txtPath(pdfpath):
    rootbasename = splitext(basename(pdfpath))[0]
    txtbasename = rootbasename + '.txt'
    return join(dirname(pdfpath), txtbasename)

def txtPath2pdfPath(txtpath):
    rootbasename = splitext(basename(txtpath))[0]
    pdfbasename = rootbasename + '.pdf'
    return join(dirname(txtpath), pdfbasename[len(txtprefix):])

def pdf2txt(pdfpath):
    txtpath = pdfPath2txtPath(pdfpath)
    # delete file if it exists
    if exists(txtpath): os.remove(txtpath)
    command = 'pdftotext "%s" "%s"' % (pdfpath, txtpath)
    print 'Executing:', command
    os.system(command)
    # Check that txt file was created
    if not exists(txtpath):
        sys.stderr.write('Failed to create txt file for pdf file: %s\n' % pdfpath)
        sys.exit(1)


illegalPathChars = r'\/:*?"<>|()'

# Memo#_Subject.pdf
def toFilePath(memo, subject, dirpath, ext):
    filename = ''
    if memo:
        filename += removeUnwantedChars(illegalPathChars, memo) + '_'
    if subject:
        filename += removeUnwantedChars(illegalPathChars, getTokens(subject, 10))
    filename += '.' + ext
    return join(dirpath, filename)


def getTokens(string, num):
    return ' '.join(string.split()[:num])

def isSublist(l1, l2):
    len1 = len(l1)
    len2 = len(l2)
    if len1 > len2: return False
    for i in range(len2-len1):
        if l1 == l2[i:i+len1]: return True
    return False

def getProgram(subjectVal):
    if subjectVal == None: return None
    tokens = subjectVal.split()
    tokens = map(canonicalize, tokens)
	#if 'somename' in tokens: return 'SomeName'

    
        for tok in tokens:
            if tok.startswith('gbr') and len(tok) == 4:
                return tok
        return None



def stripCommas(val): return filter(lambda x: x != ',', str(val))

def notBadChar(x): return not (x == '"' or x == "'")    

if __name__=='__main__':
    if len(sys.argv) < 3:
        sys.stderr.write('usage: MemoExtractor.py <txt file or directory> <csv out file>\n')
        sys.exit(1)
    inputpath = sys.argv[1]
    outfilepath = sys.argv[2]
    # Get txt paths
    txtPaths = getTxtPaths(inputpath)
    print 'writing to file:', outfilepath
    outfile = open(outfilepath, 'w')
    # write header
    outfile.write('file, subject, date, memo, to, from, program, newfile\n')
    for txtpath in txtPaths:
        print 'Processing file:', txtpath
        subject, dateObj, memo, toStr, fromStr, program = getInfoFromFile(txtpath)
        dateStr = None
        if dateObj: dateStr = time.strftime('%m/%d/%Y', dateObj)
        # Ensure no commas in values of memo file
        subject = stripCommas(subject)
        memo = stripCommas(memo)
        toStr = stripCommas(toStr)
        fromStr = stripCommas(fromStr)

        pdfpath = txtPath2pdfPath(txtpath)
        dirpath = dirname(pdfpath)
        newpath = toFilePath(memo, subject, dirpath, 'pdf')
        print 'Attempting to rename file "%s" to "%s"' % (pdfpath, newpath)
        if exists(newpath):
            print 'File %s already exists' % newpath
            newpath = None
        elif isfile(pdfpath):
            try:
                os.rename(pdfpath, newpath)
                print 'Renamed %s successfully' % pdfpath
            except IOError, msg:
                sys.stderr.write('Error renaming file %s\n' % pdfpath)
                sys.stderr.write(msg + '\n')
                newpath = None
        else:
            print 'pdf file "%s" does not exists' % pdfpath
            newpath = None
        if newpath == None: newpathStr = 'None'
        else: newpathStr = basename(newpath)
        line = ','.join(map(str,
          [txtpath, subject, dateStr, memo, toStr,
           fromStr, program, newpathStr]))
        line = filter(notBadChar, line)
        outfile.write(line + '\n')
    outfile.close()
    print 'Completed writing file:', outfilepath
