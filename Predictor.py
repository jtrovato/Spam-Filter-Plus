import time
import re
from math import log
import sys
import glob
import random
from collections import defaultdict
import nltk
import copy

class Predictor:
    '''
    Predictor which will do prediction on emails
    '''
    def __init__(self, spamFolder, hamFolder):
        self.__createdAt = time.strftime("%d %b %H:%M:%S", time.gmtime())
        self.__spamFolder = spamFolder
        self.__hamFolder = hamFolder
        self.spamProbs = []
        self.hamProbs = []
        self.spamSubjectProbs = []
        self.hamSubjectProbs = []

        # do training on spam and ham
        self.__train__()

    def __train__(self):
        '''train model on spam and ham'''
        #define the vocabularies
        vocab = defaultdict(int)
        for folder in [self.__spamFolder, self.__hamFolder]:
            vocab.update(self.files2countdict(glob.glob(folder+"/*")))
        vocab["UNKNOWN"]=0;
        vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
        
        classifiers = []
        #generate prob models and classifers
        for folder in (self.__spamFolder, self.__hamFolder):
            print folder
            vocab_countdict = defaultdict(int, vocab)
            vocab_countdict.update(self.files2countdict(glob.glob(folder+"/*")))
            #Smoothing
            total_vocab_words = sum(vocab_countdict.values())
            m = 100
            vocab_countdict = dict((word, vocab_countdict[word]+(1.0/m)) for word in vocab_countdict)
            #calculate probabilities of each word
            vocab_probdict = dict((word, float(vocab_countdict[word])/(total_vocab_words+(len(vocab_countdict)/m))) for word in vocab_countdict)
            probdict = vocab_probdict;   #weighting function
            classifiers.append(probdict)
        
        self.spamProbs = classifiers[0]
        self.hamProbs = classifiers[1]
    
    """counts occurences of each token in a list of files""" 
    def files2countdict(self, filelist):
        d = defaultdict(int)
        tknzr = Tokenizer()
        for f in filelist:
            content = open(f).read()
            tokens, bodyLength, subjectTokens, recipientsTokens, numOfRecipients = tknzr.tokenize(content)
            #tokens = tknzr.tokenizeHeader(content)
            for token in tokens:
                d[token] += 1
            d['BODYLENGTH'] = bodyLength
            d['NUMRECIPIENTS'] = numOfRecipients
        return d

    def predict(self, filename):
        '''Take in a filename, return whether this file is spam
        return value:
        True - filename is spam
        False - filename is not spam (is ham)
        '''
        # do prediction on filename
        test_content = open(filename, 'r').read()
        tknzr = Tokenizer()
        testTokens, bodyLength, subjectTokens, recipientsTokens, numOfRecipients = tknzr.tokenize(test_content)
        #test_tokens = tknzr.tokenizeHeader(test_content)
        predictions = []

        for probdict in [self.spamProbs, self.hamProbs]:
            score = 0
            for t in testTokens:
                try:
                    score += log(probdict[t])
                except KeyError:
                    score += log(probdict["UNKNOWN"])
            predictions.append(score) 
        
        #based on scores, is it spam or not?
        if predictions[0] > predictions[1]:
            return True
        else:
            return False

######### REGULAR EXPRESSIONS #########
url_re = re.compile(r""" \b (?: (?: (https? | ftp) ://)| (?= ftp\.[^\.\s<>"'\x7f-\xff] )| (?= www\.[^\.\s<>"'\x7f-\xff] ) ) ([^\s<>"'\x7f-\xff]+)""", re.VERBOSE)

html_re = re.compile(r""" < (?![\s<>]) [^>]{0,256} > """, re.VERBOSE | re.DOTALL)

breaking_entity_re = re.compile(r""" &nbsp; | < (?: p | br ) > """, re.VERBOSE)

punctuation_re = re.compile(r'\W+')

subject_re = re.compile(r'''(?<=subject:)(.*)(?=\r\n)''')

recipient_re = re.compile(r'''(?<=to:)(.*)(?=\r\n)''')

#class used to take out unwanted html tags
class Stripper(object):
    separator = ''

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def analyze(self, text):
        i = 0
        retainedText = []
        tempText = retainedText.append
        while True:
            m = self.start(text, i)
            if not m:
                tempText(text[i:])
                break
            start, end = m.span()
            tempText(text[i : start])
            m = self.end(text, end)
            if not m:
                tempText(text[start:])
                break
            temp, i = m.span()
        return self.separator.join(retainedText)

######### TOKENIZER CLASS #########
class Tokenizer():

  def tokenize(self, message):
    header, body = self.seperateMessage(message)
    subjectTokens, recipientsTokens, numOfRecipients = self.tokenizeHeader(header)
    bodyTokens, bodyLength = self.tokenizeBody(body)
    return (bodyTokens, bodyLength, subjectTokens, recipientsTokens, numOfRecipients)

  def seperateMessage(self, message):
    splitTuple = message.partition('\r\n\r\n')
    return (splitTuple[0], splitTuple[2])

  def tokenizeBody(self, message):
    tokens = []

    text = message.lower()
    bodyLength = len(text)
  
    text = url_re.sub(' ', text) #removes URLS
    text = Stripper(re.compile(r"< \s* style\b [^>]* >", re.VERBOSE).search,re.compile(r"</style>").search).analyze(text) #removes content between <style> tags
    text = Stripper(re.compile(r"<!--|<\s*comment\s*[^>]*>").search, re.compile(r"-->|</comment>").search).analyze(text) #removes content between <comment> tags
    text = Stripper(re.compile(r"<\s*noframes\s*>").search, re.compile(r"</noframes\s*>").search).analyze(text) #removes content between <noframes> tags
    
    text = breaking_entity_re.sub(' ', text) #removes HTML tags
    text = html_re.sub(' ', text) #removes HTML
    #text = punctuation_re.sub(' ', text) #removes punctuation 

    interTokens = nltk.word_tokenize(text)

    for word in interTokens:
      if len(word) > 3 and len(word) < 13:
        if word[-1:] == 's':
          tokens.append(word[:-1])
        else:
          tokens.append(word)
    return (tokens, bodyLength)

  def tokenizeHeader(self, message):

    text = message.lower()
    subject = subject_re.findall(text)
    if (len(subject) > 0):
        subject = nltk.word_tokenize(subject[0])
    
    recipients = recipient_re.findall(text)
    numOfRecipients = 0
    recipientsTokens = []
    if (len(subject) > 0):
        for recipient in recipients:
            numOfRecipients += 1
            recipient = punctuation_re.sub(' ', recipient)
            recipientsTokens.append(nltk.word_tokenize(recipient))
    recipientsTokens = [item for sublist in recipientsTokens for item in sublist]

    return (subject, recipientsTokens, numOfRecipients)

def classifyFiles(filelist, testdir):
        count = 0
        spamcount = 0
        hamcount = 0
        for testfile in filelist:
            count += 1
            print testfile,
            spam_pred = nbsf.predict(testfile)
            print spam_pred
            
            
            if count <= 200:
                if spam_pred == False:
                    hamcount += 1
            else:
                if spam_pred == True:
                    spamcount += 1


            percentspam = (float(spamcount)/count)*100
            percentham = (float(hamcount)/count)*100
        if testdir == 'hw6-spamham-data/dev/':
            print 'recognized ' + str(spamcount) + ' spam emails ' + str((float(spamcount)/200)*100) + '%'
            print 'recognized ' + str(hamcount) + ' ham emails ' + str((float(hamcount)/200)*100) + '%'
        else:
            print 'spam: ' + str(spamcount) + ' ' + str(percentspam) + '%' 
            print 'ham: ' + str(hamcount) + ' ' + str(percentham) + '%'

if __name__ == '__main__':
    print "usage:", sys.argv[0], "devdir"
    nbsf = Predictor('hw6-spamham-data/spam/', 'hw6-spamham-data/ham/')
    testdir = sys.argv[-1]
    print testdir
    filelist = glob.glob(testdir+"/*")
    filelist_final = filelist
    #if testdir == 'hw6-spamham-data/dev/':
      filelist = dict((name[-3:], name) for name in filelist)
      for num in filelist.keys():
        value = filelist[num];
        if num[0:2] == 'ev':
            filelist['00' + num[2]] = value
            del filelist[num]
        elif num[0:1] == 'v':
            filelist['0' + num[1:]] = value
            del filelist[num]
        sorted_filelist = sorted(filelist)
        filelist_final = list(filelist[key] for key in sorted_filelist)    
    #else:
        filelist_final = filelist

    classifyFiles(filelist_final, testdir)
