import urllib.request
import configparser
import csv
import sqlalchemy
import json
import traceback
import time
from bs4 import BeautifulSoup
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO, TextIOWrapper
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from twitter import *
from zipfile import ZipFile

config = configparser.ConfigParser()
config.read("config.cfg")

def setupTwitter():
     return(Twitter(auth=OAuth(
	config["twitter"]["access_token_key"],
	config["twitter"]["access_token_secret"],
	config["twitter"]["consumer_key"],
	config["twitter"]["consumer_secret"]
)))

def sendTwit(message):
     twitterapi = setupTwitter()
     twitterapi.statuses.update(status=message)

urls = {
	"base": "http://www.nemweb.com.au/",
	"p5": "http://www.nemweb.com.au/Reports/CURRENT/P5_Reports/",
	"dispatchis": "http://www.nemweb.com.au/Reports/CURRENT/DispatchIS_Reports/",
	"notices": "http://www.nemweb.com.au/Reports/CURRENT/Market_Notice/"
}

engine = create_engine(config["database"]["dbstring"])
Base = declarative_base()

class Downloads(Base):
     __tablename__ = 'downloads'
     url = Column(String(255), primary_key=True)

class P5(Base):
     __tablename__ = 'p5'
     datetime = Column(DateTime, primary_key=True)
     regionid = Column(String(100), primary_key=True)
     rrp = Column(Float)
     demand = Column(Float)
     generation = Column(Float)

class dispatchIS(Base):
     __tablename__ = 'dispatchIS'
     datetime = Column(DateTime, primary_key=True)
     regionid = Column(String(100), primary_key=True)
     rrp = Column(Float)
     demand = Column(Float)
     generation = Column(Float)
class notices(Base):
     __tablename__ = 'notices'
     id = Column(Integer, primary_key=True)
     datetime = Column(DateTime)
     message = Column(String(500))
     url = Column(String(255))
      

        
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)
session = Session()

def urlDownloaded(url):
    if session.query(Downloads.url).filter(Downloads.url==urls['base'] +url).count() > 0:
        return True
    else:
        return False

#returns list of P5 files as an array of urls
def listP5Files():
    p5urls=[]
    indexpage = urllib.request.urlopen(urls['p5']).read()
    soup = BeautifulSoup(indexpage)
    for link in soup.find_all('a'):
        url = link.get('href').lstrip("/")
        if url[-4:] == ".zip" and urlDownloaded(url) == False:
            p5urls.append(urls['base'] + url)
    return p5urls

def processP5():
    for url in listP5Files():
        try:
                print("Downloading " + url)
                files = ZipFile(BytesIO(urllib.request.urlopen(url).read()))
                data = files.read(files.namelist()[0])
                data = data.decode('utf-8').split("\n")
                csvfile = csv.reader(data)
                for row in csvfile:
                        try:
                                if row[0] == "I" and row[1] == "P5MIN" and row[2] == "REGIONSOLUTION":
                                        columns = row
                                elif row[2] == "REGIONSOLUTION":
                                        p5value = {
                               "datetime" : datetime.strptime(row[columns.index("INTERVAL_DATETIME")], "%Y/%m/%d %H:%M:%S"),
                               "regionid" : row[columns.index("REGIONID")],
                               "rrp" : row[columns.index("RRP")],
                               "demand" : row[columns.index("TOTALDEMAND")],
                               "generation" : row[columns.index("AVAILABLEGENERATION")] 
                               }
                                        p5dbobject = P5(**p5value)
                                        session.merge(p5dbobject)
                        except(IndexError):
                                pass
                session.merge(Downloads(url=url))
                session.commit()
        except Exception as e:
            session.merge(Downloads(url=url))
            session.commit()
            print(traceback.format_exc())
        
def listDispatchISFiles():
    dispatchisurls=[]
    indexpage = urllib.request.urlopen(urls['dispatchis']).read()
    soup = BeautifulSoup(indexpage)
    for link in soup.find_all('a'):
        url = link.get('href').lstrip("/")
        if url[-4:] == ".zip"  and urlDownloaded(url) == False:
            dispatchisurls.append(urls['base'] + url)
    return dispatchisurls
    
def processDispatchIS():
    for url in listDispatchISFiles():
        try:
                print("Downloading " + url)
                files = ZipFile(BytesIO(urllib.request.urlopen(url).read()))
                data = files.read(files.namelist()[0])
                data = data.decode('utf-8').split("\n")
                csvfile = csv.reader(data)
                for row in csvfile:
                    try:
                        if row[0] == "I" and row[1] == "DISPATCH" and row[2] == "PRICE":
                                    columnsprice = row
                        elif row[2] == "PRICE":
                                    dispatchISvalue = {
                               "datetime" : datetime.strptime(row[columnsprice.index("SETTLEMENTDATE")],"%Y/%m/%d %H:%M:%S"),
                               "regionid" : row[columnsprice.index("REGIONID")],
                               "rrp" : row[columnsprice.index("RRP")]
                               }
                                    dispatchISobject = dispatchIS(**dispatchISvalue)
                                    session.merge(dispatchISobject)
                        elif row[0] == "I" and row[1] == "DISPATCH" and row[2] == "REGIONSUM":
                                    columnsdemand = row
                        elif row[2] == "REGIONSUM":
                                    dispatchISvalue = {
                               "datetime" : datetime.strptime(row[columnsdemand.index("SETTLEMENTDATE")],"%Y/%m/%d %H:%M:%S"),
                               "regionid" : row[columnsdemand.index("REGIONID")],
                               "demand" : row[columnsdemand.index("TOTALDEMAND")],
                               "generation" : row[columnsdemand.index("AVAILABLEGENERATION")] 
                               }
                                    dispatchISobject = dispatchIS(**dispatchISvalue)
                                    session.merge(dispatchISobject)
                    except(IndexError):
                        pass
                session.merge(Downloads(url=url))
                session.commit()
        except Exception as e:
            session.merge(Downloads(url=url))
            session.commit()
            print(traceback.format_exc())

#returns list of P5 files as an array of urls
def listNotices():
    noticesurls=[]
    indexpage = urllib.request.urlopen(urls['notices']).read()
    soup = BeautifulSoup(indexpage)
    for link in soup.find_all('a'):
        url = link.get('href').lstrip("/")
        if url[-1] != "/" and urlDownloaded(url) == False:
            noticesurls.append(urls['base'] + url)
    return noticesurls

def processNotices():
    for url in listNotices():
        try:
            print("Downloading " + url)
            data = urllib.request.urlopen(url).read().decode('iso-8859-1','ignore')
            data = data.split("\n")
            amount = ""
            for line in data:
                if "Creation Date" in line:
                    date = line.split(":",1)[-1].strip()
                elif "Notice ID" in line:
                    id = int(line.split(":",1)[-1].strip())
                elif "External Reference" in line:
                    notice = line.split(":",1)[-1].strip()
                    notice = notice.replace("Reclassification ","#reclass ")
                    notice = notice.replace("Non-Credible ","#non_cred ")
                    notice = notice.replace("Event ","evnt ")
                    notice = notice.replace("Queensland ","qld ")
                    notice = notice.replace("Cancellation ","#cancel ")
                    notice = notice.replace("Contingency ","#contigency ")
                    notice = notice.replace("Cessation ","#cease ")
                    notice = notice.replace("Revision ","#revise ")
                    notice = notice.replace("Region "," ")
                elif "Constraint:" in line:
                    constraint = line.split(":",1)[-1].strip()
                    constraint = constraint.replace("-", "_")
                    if amount:
                        notice = "#" + constraint + " " + amount + " - " + notice
                    else:
                        notice = "#" + constraint + " - " + notice
                elif "Amount:" in line:
                    amount = line.split(":",1)[-1].strip()
            urlviewer=url.replace("http://www.nemweb.com.au/Reports/CURRENT/Market_Notice/","http://nem.mwheeler.org/notice/")
            sendTwit(notice[:115] + "... " + urlviewer)
            msgtime = datetime.strptime(date,'%d/%m/%Y     %H:%M:%S')
            session.merge(notices(id=id, datetime=msgtime, message=notice, url=url))
            session.merge(Downloads(url=url))
            session.commit()
        except Exception as e:
            session.merge(Downloads(url=url))
            session.commit()
            print(traceback.format_exc())

        
while 1:
    try:
#P5 not used yet - skip that check
#            processP5()
            processDispatchIS()
            processNotices()
            time.sleep(30)
    except Exception as e:
            print(traceback.format_exc())
