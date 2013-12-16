import time
import glob
import random


class Predictor:
    '''
    Predictor which will do prediction on emails
    '''
    def __init__(self, spamFolder, hamFolder):
        self.__createdAt = time.strftime("%d %b %H:%M:%S", time.gmtime())
        self.__spamFolder = spamFolder
        self.__hamFolder = hamFolder
        # do training on spam and ham
        self.__train__()

    def __train__(self):
        '''train model on spam and ham'''
        # the following code is only an naive example,
        # implement your own training methond here
        spamCount = len(glob.glob(self.__spamFolder+'/*'))
        hamCount = len(glob.glob(self.__hamFolder+'/*'))
        self.__spamFrequency = 1.0*spamCount/(spamCount+hamCount)

        #tokenize

        #generate prob models

        

    def predict(self, filename):
        '''Take in a filename, return whether this file is spam
        return value:
        True - filename is spam
        False - filename is not spam (is ham)
        '''
        # do prediction on filename
        #tokenize test file
        


        if random.random() <= self.__spamFrequency:
            return True
        else:
            return False

######### REGULAR EXPRESSIONS #########
url_re = re.compile(r""" \b (?: (?: (https? | ftp) ://)| (?= ftp\.[^\.\s<>"'\x7f-\xff] )| 
      (?= www\.[^\.\s<>"'\x7f-\xff] ) ) ([^\s<>"'\x7f-\xff]+)
  """, re.VERBOSE)

html_re = re.compile(r""" < (?![\s<>]) [^>]{0,256} > """, re.VERBOSE | re.DOTALL)

breaking_entity_re = re.compile(r""" &nbsp; | < (?: p | br ) > """, re.VERBOSE)

punctuation_re = re.compile(r'\W+')

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
  	header, body = seperateMessage(message)
  	headerTokens = tokenizeHeaders(header)
  	bodyTokens = tokenizeBody(body)
  	return headerTokens, bodyTokens

  def tokenizeBody(self, message):
    tokens = []
    #mess = open(message).read()
    #text = mess.lower()

    text = message.lower()
  
    text = url_re.sub(' ', text) #removes URLS
    text = Stripper(re.compile(r"< \s* style\b [^>]* >", re.VERBOSE).search,
                          re.compile(r"</style>").search).analyze(text) #removes content between <style> tags
    text = Stripper(re.compile(r"<!--|<\s*comment\s*[^>]*>").search,
                          re.compile(r"-->|</comment>").search).analyze(text) #removes content between <comment> tags
    text = Stripper(re.compile(r"<\s*noframes\s*>").search,
                          re.compile(r"</noframes\s*>").search).analyze(text) #removes content between <noframes> tags
    text = breaking_entity_re.sub(' ', text) #removes HTML tags
    text = html_re.sub(' ', text) #removes HTML
    text = punctuation_re.sub(' ', text) #removes punctuation 

    interTokens = nltk.word_tokenize(text)

    for word in interTokens:
      if len(word) > 3 and len(word) < 13:
        if word[-1:] == 's':
          tokens.append(word[:-1])
        else:
          tokens.append(word)
    #print tokens
    return tokens

  def tokenizeHeaders(self, message):
    tokens = []
    return tokens



