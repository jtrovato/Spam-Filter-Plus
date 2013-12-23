import time
import re
from math import log
import sys
import glob
import random
from collections import defaultdict
import nltk
import copy
import operator

class Predictor:
    '''
    Predictor which will do prediction on emails
    '''
    def __init__(self, spamFolder, hamFolder):
        self.__createdAt = time.strftime("%d %b %H:%M:%S", time.gmtime())
        self.__spamFolder = spamFolder
        self.__hamFolder = hamFolder
        self.spamProbs = []
        self.spamSubProbs = []
        self.spamlength = 0
        self.hamlength = 0
        self.hamProbs = []
        self.hamSubProbs = []
        self.spamSubjectProbs = []
        self.hamSubjectProbs = []

        # do training on spam and ham
        self.__train__()

    def __train__(self):
        '''train model on spam and ham'''
        #define the vocabularies
        vocab = defaultdict(int)
        subvocab = defaultdict(int)
        for folder in [self.__spamFolder, self.__hamFolder]:
            body_d, sub_d = self.files2countdict(glob.glob(folder+"/*"))
            vocab.update(body_d)
            subvocab.update(sub_d)
        vocab["UNKNOWN"]=0;
        subvocab['UNKNOWN']=0;
        vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
        subvocab = defaultdict(int, zip(subvocab.iterkeys(), [0 for i in subvocab.values()]))
        
        classifiers = []
        #generate prob models and classifers
        for folder in (self.__spamFolder, self.__hamFolder):
            print folder
            vocab_countdict = defaultdict(int, vocab)
            sub_countdict = defaultdict(int, subvocab)
            body_d, sub_d = self.files2countdict(glob.glob(folder+"/*"))
            vocab_countdict.update(body_d)
            sub_countdict.update(sub_d)
            #get classifiers that do not need smoothing i.e. length
            if folder == self.__spamFolder:
                self.spamLength = vocab_countdict['CLASSLENGTH']
            else:
                self.hamLength = vocab_countdict['CLASSLENGTH']
            del vocab_countdict['CLASSLENGTH']
            del vocab_countdict['NUMRECIPIENTS']
            #weight the length of the email
            
            #Smoothing 
            total_vocab_words = sum(vocab_countdict.values())
            total_sub_words = sum(sub_countdict.values())
            m = 100
            vocab_countdict = dict((word, vocab_countdict[word]+(1.0/m)) for word in vocab_countdict)
            sub_countdict = dict((word, sub_countdict[word]+(1.0/m)) for word in sub_countdict)
            #calculate probabilities of each word
            
            vocab_probdict = dict((word, float(vocab_countdict[word])/(total_vocab_words+(len(vocab_countdict)/m))) for word in vocab_countdict)
            sub_probdict =  dict((word, float(sub_countdict[word])/(total_sub_words+(len(sub_countdict)/m))) for word in sub_countdict) 
            probdict = vocab_probdict;   #weighting function
            classifiers.append(vocab_probdict)
            classifiers.append(sub_probdict)
        
        self.spamProbs = classifiers[0]
        self.spamSubProbs = classifiers[1]
        self.hamProbs = classifiers[2]
        self.hamSubProbs = classifiers[3]
    
    """counts occurences of each token in a list of files""" 
    def files2countdict(self, filelist):
        body_d = defaultdict(int)
        sub_d = defaultdict(int)
        tknzr = Tokenizer()
        classlength = 0
        for f in filelist:
            content = open(f).read()
            tokens, bodyLength, subjectTokens, recipientsTokens, numOfRecipients = tknzr.tokenize(content)
            classlength += bodyLength
            for token in tokens:
                body_d[token] += 1
            
            body_d['CLASSLENGTH'] = classlength
            body_d['NUMRECIPIENTS'] = numOfRecipients
            for token in subjectTokens:
                sub_d[token] += 1
        return (body_d, sub_d)

    def predict(self, filename):
        '''Take in a filename, return whether this file is spam
        return value:
        True - filename is spam
        False - filename is not spam (is ham)
        '''
        # do prediction on filename
        test_content = open(filename, 'r').read()
        tknzr = Tokenizer()
        bodyTokens, bodyLength, subjectTokens, recipientsTokens, numOfRecipients = tknzr.tokenize(test_content)
        prob_spam = float(self.spamLength)/(self.spamLength + self.hamLength)
        prob_ham = float(self.hamLength)/(self.spamLength + self.hamLength)
        predictions = []
        
        for probdict in [self.spamProbs, self.hamProbs]: #for each class
            score = 0
            subscore = 0
            if probdict == self.spamProbs:
                subdict = self.spamSubProbs
            else:
                subdict = self.hamSubProbs

            for t in bodyTokens: #for each feature calcualte P(x|c)
                try:
                    score += log(probdict[t]) #sum the log probs 
                except KeyError:
                    score += log(probdict["UNKNOWN"])

            for t in subjectTokens:
                try:
                    subscore += log(subdict[t])
                except KeyError:
                    subscore += log(probdict["UNKNOWN"])
            #add in other features
            score = score + subscore      
            #multiply by P(c)
            if probdict == self.hamProbs:
                score += log(prob_ham) 
            else:
                score += log(prob_spam)
            
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

    #text = message.lower()
    text = message
    #bodyLength = len(text) #chararters
  
    text = url_re.sub(' ', text) #removes URLS
    text = Stripper(re.compile(r"< \s* style\b [^>]* >", re.VERBOSE).search,re.compile(r"</style>").search).analyze(text) #removes content between <style> tags
    text = Stripper(re.compile(r"<!--|<\s*comment\s*[^>]*>").search, re.compile(r"-->|</comment>").search).analyze(text) #removes content between <comment> tags
    text = Stripper(re.compile(r"<\s*noframes\s*>").search, re.compile(r"</noframes\s*>").search).analyze(text) #removes content between <noframes> tags
    
    text = breaking_entity_re.sub(' ', text) #removes HTML tags
    text = html_re.sub(' ', text) #removes HTML
    text = punctuation_re.sub(' ', text) #removes punctuation 

    interTokens = nltk.word_tokenize(text)

    for word in interTokens:
      
      if len(word) > 0 and len(word) < 13:
        if word[-1:] == 's':
          tokens.append(word[:-1])
        else:
          tokens.append(word)
      else:
        if word == '!':
          tokens.append(word)
    
    bodyLength = len(tokens) #tokens/words
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
            
            if testdir == 'hw6-spamham-data/dev/': 
                if count <= 200:
                    if spam_pred == False:
                        hamcount += 1
                else:
                    if spam_pred == True:
                        spamcount += 1
            else:
                if spam_pred == False:
                        hamcount += 1
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
    filelist = dict((name[-3:], name) for name in filelist)
    for num in filelist.keys():
        value = filelist[num];
        if num[0:2] in ['ev', 'am']:
            filelist['00' + num[2]] = value
            del filelist[num]
        elif num[0:1] in ['v', 'm']:
            filelist['0' + num[1:]] = value
            del filelist[num]
        sorted_filelist = sorted(filelist)
        filelist_final = list(filelist[key] for key in sorted_filelist)    

    classifyFiles(filelist_final, testdir)
