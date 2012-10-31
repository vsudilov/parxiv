import traceback
import os,sys
#---------------------------------------
#Setup logging
import logging
import logging.handlers
filename = os.path.join(os.path.expanduser('~'),'logs/parxiv.log')
logfmt = '%(levelname)s:  %(message)s\t(%(asctime)s)'
datefmt= '%m/%d/%Y %I:%M:%S %p'
formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
logger = logging.getLogger('__main__')
logging.root.setLevel(logging.DEBUG)

#ch = logging.StreamHandler() #console handler
#ch.setFormatter(formatter)
#if not os.path.isdir("logs"): os.mkdir("logs")
fh = logging.FileHandler(filename=filename) #file handler
fh.setFormatter(formatter)
rfh = logging.handlers.RotatingFileHandler(filename=filename,maxBytes=1000000,backupCount=5)
rfh.setFormatter(formatter)
#logger.addHandler(ch)
#logger.addHandler(fh) 
logger.addHandler(rfh)
#Print tracebacks to the logfile
def dumpTraceback(filename=os.devnull):
  fp = open(filename,'a')
  traceback.print_exc(file=fp)
  fp.close()
#---------------------------------------


  


class arxiv_page:
  def __init__(self,page='http://arxiv.org/list/astro-ph/new'):
    self.page = page    
    self.downloaded = False


  def __remove_punctuation(self,string,punctuation=['?','!','.',',','"','>','<','[',']','{','}',')','(']):
    for i in punctuation:
      string = string.replace(i,'')
    return string



  def __parse_titles(self):
    titles = []
    soup = self.soup
    for i in soup.find_all('div',class_='list-title'):
      title = i.find_all('span')[0].nextSibling.strip()
      title = self.__remove_punctuation(title)
      titles.extend(title.split())
    return titles


  def __parse_authors(self):
    authors = []
    soup = self.soup
    for i in soup.find_all('div',class_='list-authors'):
      for j in i.find_all('a'):
        authors.extend(j.text)
    return authors


  def __parse_abstracts(self):
    words = []
    soup = self.soup
    for i in soup.find_all('p')[:-1]:
      abstract = i.text.strip()
      abstract = abstract.replace('\n',' ')
      abstract = self.__remove_punctuation(abstract)
      words.extend(abstract.split())
    return words

  def __histogram(self,words,ignored_words=[]):
    hist = {}
    for word in words:
      word = word.lower()
      if word in ignored_words:
        continue
      hist[word] = hist.get(word, 0) + 1    
    return hist


  def download(self):
    if self.downloaded:
      msg = "Warning: Download request on an already downloaded page"
      try:
        logger.warning(msg)
      except (NameError,AttributeError):
        print msg

    from urllib2 import urlopen
    from bs4 import BeautifulSoup
    raw_html = urlopen(self.page).read()
    self.soup = BeautifulSoup(raw_html)
    self.downloaded = True



  def parse(self,titles=True,abstracts=True,authors=True,ignored_words=["we","the","a","an","in","be","would","of","that", \
                                                                         "are","is","to","with","for","all","by","further", \
                                                                         "at","also","for","too","or","which","they","between", \
                                                                         "this","their"]):
      if not self.downloaded:
        self.download()
       
      words,authors,titles = [],[],[]
      self.hist = {}
      if titles:
        titles.extend(self.__parse_titles())  
        self.hist['titles'] = self.__histogram(titles,ignored_words=ignored_words)
    
      if abstracts:      
        words.extend(self.__parse_abstracts())
        self.hist['abstracts'] = self.__histogram(words,ignored_words=ignored_words)

      if authors:      
        authors.extend(self.__parse_authors())
        self.hist['authors'] = self.__histogram(authors,ignored_words=ignored_words)
  
      
      


def main():

  page = arxiv_page()
  page.download()
  page.parse()
  
  '''
  from Stackoverflow, how to represent a sorted dict based value
  
  import operator
  x = {1: 2, 3: 4, 4:3, 2:1, 0:0}
  sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1))
  '''


if __name__ == "__main__":
  try:
    main()
  except:
    dumpTraceback(filename)

