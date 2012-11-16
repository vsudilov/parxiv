#!/usr/bin/env python
'''
USAGE: parxiv.py database

Creates a histogram of words in the titles,abstracts,and authors of the the arxiv astro-PH "new" page and stores this in <database>.
'''


import traceback
import os,sys
import datetime
import sqlite3
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

ch = logging.StreamHandler() #console handler
ch.setFormatter(formatter)
if not os.path.isdir(os.path.join(os.path.expanduser('~'),"logs")): 
  os.mkdir(os.path.join(os.path.expanduser('~'),"logs"))
fh = logging.FileHandler(filename=filename) #file handler
fh.setFormatter(formatter)
rfh = logging.handlers.RotatingFileHandler(filename=filename,maxBytes=1000000,backupCount=5)
rfh.setFormatter(formatter)
logger.addHandler(ch)
#logger.addHandler(fh) 
logger.addHandler(rfh)
#Print tracebacks to the logfile
def dumpTraceback(filename=os.devnull):
  fp = open(filename,'a')
  traceback.print_exc(file=fp)
  traceback.print_exc()
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

  def __parse_date(self):
    soup = self.soup
    return soup.find_all('div',class_='list-dateline')[0].text
   
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
        authors.append(j.text)
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
    self.date_line = self.__parse_date()
    self.downloaded = True



  def parse(self,titles=True,abstracts=True,authors=True, ignored_words=["we","the","a","an","in",
     "be","would","of","that","are","is","to","with","for","all","by","further", 
     "at","also","from","too","or","which","they","between","this","their","we",
     "our","these","its","it","using","has","have","than","on","and","will","as",
     "can","not","cannot","where","but","into","use","used"]):
    
    
    if not self.downloaded:
      self.download()
     
    words,a,t = [],[],[]
    self.hist = {}
    if titles:
      t.extend(self.__parse_titles())  
      self.hist['titles'] = self.__histogram(t,ignored_words=ignored_words)

    if abstracts:      
      words.extend(self.__parse_abstracts())
      self.hist['abstracts'] = self.__histogram(words,ignored_words=ignored_words)

    if authors:      
      a.extend(self.__parse_authors())
      self.hist['authors'] = self.__histogram(a,ignored_words=ignored_words)


def checkLastScrape(page,file='parxiv.last'):
  with open(file,'r') as fp:
    last = fp.read()
    if last == page.date_line:
      logger.info("Same date-line as previous parse. Exiting")
      sys.exit(0)
  with open(file,'w') as fp:
    fp.write(page.date_line)
      
def init_db(db):
  logger.info("Initialized database [%s] for the first time." % db)
  db = sqlite3.connect(db)
  db.execute('CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, word TEXT, count INTEGER)')      
  db.execute('CREATE TABLE titles (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, word TEXT, count INTEGER)')  
  db.execute('CREATE TABLE abstracts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, word TEXT, count INTEGER)')  
  db.commit()


def main(argv=sys.argv):
  if not argv or len(argv) != 2:
    sys.exit(__doc__)
  db = argv[1]
  if not os.path.exists(db):
    init_db(db) 
  db = sqlite3.connect(db)

  if not os.path.exists('parxiv.last'):
    open('parxiv.last','w').close()

  page = arxiv_page()
  page.download()
  page.parse()
  checkLastScrape(page)
  
  today = datetime.date.today().isoformat() 
  for tbl_name in page.hist.keys():
    for word,count in page.hist[tbl_name].iteritems():
      db.execute('INSERT INTO %s (date,word,count) VALUES (?,?,?)' % tbl_name,(today,word,count))
  db.commit()
  logger.info("Finished parse of page and update of database")
  
  '''
  from Stackoverflow: how to represent a sorted dict based value
  
  import operator
  x = {1: 2, 3: 4, 4:3, 2:1, 0:0}
  sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1))
  '''


if __name__ == "__main__":
  try:
    main()
  except SystemExit:
    pass
  except:
    dumpTraceback(filename)

