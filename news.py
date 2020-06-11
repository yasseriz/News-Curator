# Include necessary libraries
from bs4 import BeautifulSoup
import urllib.request as url
import re
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk import sent_tokenize
from nltk.corpus import stopwords
from nltk import word_tokenize
stop_word = stopwords.words('english')
import string
import requests 
import pandas as pd
import heapq
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apiData import SENDGRID_API_KEY
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# URL of news site used
url = 'https://www.theverge.com'

response = requests.get(url)
content = BeautifulSoup(response.content, 'lxml')

# Parsing through HTML to find headlines
elements =  content.find_all('h2', {"class":"c-entry-box--compact__title"})

# Obtaining title and link to full article for each headline and storing in a dictionary
temp = dict()
for ele in elements:
    title = ele.get_text()
    link = ele.find('a', href=True)
    temp[title] = link['href']

df = pd.DataFrame(temp.items(), columns=['title', 'link'])

count = 0
# Iterating through each row in the dataframe
for row in df.head(6).itertuples():

    # Visiting each article
    article = requests.get(row.link)
    content = BeautifulSoup(article.content, 'lxml')
    paragraph = content.find_all('p')
    tempParagraph = ''

    for line in paragraph:
        tempParagraph += (line.text)
    
    # Cleaning up text
    processed = tempParagraph.replace(r'^\s+|\s+?$','')
    processed = processed.replace('\n',' ')
    processed = processed.replace("\\",'')
    processed = processed.replace(",",'')
    processed = processed.replace('"','')
    processed = re.sub(r'\[[0-9]*\]','',processed)
    
    # Tokenizing words and calculating the frequency of each word
    sentences = sent_tokenize(processed)
    frequency = {}
    processed1 = processed.lower()
    for word in word_tokenize(processed1):
        if word not in stop_word and word not in string.punctuation:
            if word not in frequency.keys():
                frequency[word]=1
            else:
                frequency[word]+=1

    # Calculating the importance of every word
    max_fre = max(frequency.values())
    for word in frequency.keys():
        frequency[word]=(frequency[word]/max_fre)

    # Calculating the importance of every sentence in the article
    sentence_score = {}
    for sent in sentences:
        for word in word_tokenize(sent):
            if word in frequency.keys():
                if len(sent.split(' '))<30:
                    if sent not in sentence_score.keys():
                        sentence_score[sent] = frequency[word]
                    else:
                        sentence_score[sent]+=frequency[word]
    
    # Finding sentences with 4 highest scores and displaying them
    summary = heapq.nlargest(4,sentence_score,key = sentence_score.get)
    summary = ' '.join(summary)
    final = "SUMMARY:- \n  " +summary
    textfinal = 'TEXT:-    '+processed
    textfinal = textfinal.encode('ascii','ignore')
    textfinal = str(textfinal)

    df.loc[count,'Summary']=summary
    count+=1
    print("*************************")
    
# Sending email
message = Mail(
    from_email='yasserizaheer@gmail.com',
    to_emails='yasserizaheer@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)