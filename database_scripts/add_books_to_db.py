import sys

import re
import string

from datetime import datetime
from threading import Thread

import mongoengine

from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
from gutenberg.query import get_etexts
from gutenberg.query import get_metadata

import model
import extract_metadata


def process_book_wait(book_object):
    thread = Thread(target=process_book, args=(book_object,))
    thread.start()
    thread.join()

def process_book(book_object):
    text = book_object.text
    passages = get_passages_from_text(text)
    for passage_index, passage in enumerate(passages):
        passage_utf8 = passage.encode('utf-8')
        passage_object = model.Passage(parent_doc=book_object, passage_text=passage_utf8).save()
        for word in passage.split(' '):
            word = word.translate(None, punctuation_droplist).lower()
            word_object = model.Word.get_word_object(word)
            if(word_object is not None):
                word_object.update(add_to_set__passages=passage_object)

def get_passages_from_text(text):
    sentences = split_into_sentences(text.encode('ascii'))
    passages = construct_passages(sentences)
    return passages

def split_into_sentences(text):
    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(". ",".<stop>")
    text = text.replace("? ","?<stop>")
    text = text.replace("! ","!<stop>")
    text = text.replace("\"?","?\"")
    text = text.replace("\"!","!\"")
    text = text.replace("\".",".\"")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences    

def construct_passages(text):
    passages = []
    temp_passage = ""
    for sentence in sentences:
        temp_passage = temp_passage + " " + sentence
        if((len(temp_passage) >= 200) and (len(temp_passage) <= 750)):
            passages.append(temp_passage.strip())
            temp_passage = ""
        elif(len(temp_passage) < 200): continue
        elif(len(temp_passage) > 750):
            temp_passage = ""
    return passages

if __name__ == '__main__':
	
    min_word_length = 4

    print "Loading books..."
    tstart = datetime.now()

    punctuation_droplist = string.punctuation.replace("-", "")

    with open('books.txt', 'r') as f:
        books = []
        for line in f:
            books.append(int(line.rstrip()))

    metadata = extract_metadata.execute()
    for book in books:
        text = strip_headers(load_etext(book)).strip()
        text = text.replace('\n\n', '') # get rid of paragraph breaks
        text = text.replace('\n', ' ') # get rid of arbitrary newlines
        title =  metadata[book]['title']
        author = metadata[book]['author']
        try:
            text_utf8 = text.encode('utf-8')
            title_utf8 = title.encode('utf-8')
            author_utf8 = author.encode('utf-8')
            doctype_utf8 = u'book'.encode('utf-8')
            book_object = model.Parent_Document(text=text_utf8, title=title_utf8, author=author_utf8, url=author_utf8, doctype=doctype_utf8).save()
            process_book_wait(book_object)
        except mongoengine.NotUniqueError:
            print "Book " + title + " by " + author + " already in database. Book skipped. If you would like to reload, please first delete."
            continue
        print "Finished with " + title + " by " + author

    tend = datetime.now()
    print "Loaded books: Total time: " + str((tend-tstart).seconds)