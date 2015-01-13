from flask import Flask, render_template 
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker 
from datetime import timedelta, datetime
import flask 
import mysql.connector
import urllib.request
from io import BytesIO 
import re 
import configparser
 
app = Flask(__name__) 
app.debug = True 

config = configparser.ConfigParser()
config.read("config.cfg")


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
     def as_dict(self):
          return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class notices(Base):  
     __tablename__ = 'notices'  
     id = Column(Integer, primary_key=True)  
     datetime = Column(DateTime)  
     message = Column(String(500))  
     url = Column(String(255))  
  
  
  
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()




def dictfetchall(cursor):
    # Returns all rows from a cursor as a list of dicts
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) 
            for row in cursor.fetchall()]

def prettyNotice(noticeText):
    noticeText = re.sub(r"\r?\n-+\r?\nEND OF REPORT\r?\n-+", r"", noticeText)
    noticeText = re.sub(r"-+\r?\n(.+)\r?\n-+\r?\n", r"\n<h1>\1</h1>", noticeText)
    noticeText = re.sub(r"\r?\n-+\r?\n", r"\n<hr>", noticeText)
    noticeText = re.sub(r"\n([^\n\r:]+):\r?\n", r"<h2>\1</h2>", noticeText)
    noticeText = re.sub(r"\r?\n(.{3,30}):(.+)", r"\n<tr><td><b>\1 :</b></td><td>\2</td></tr>", noticeText)
    noticeText = re.sub(r"((<tr>.+</tr>\r?\n)+)", r"<table>\1</table>", noticeText)
    noticeText = re.sub(r"\r?\n\r?\n", r"\n<br>", noticeText)
    noticeText = re.sub(r"(.*)[^>]\r?\n", r"\1<br>\n", noticeText)
    noticeText = "<html><head><style>body {font-family: Sans-Serif;}</style></head><body>" + noticeText
    noticeText = noticeText + "</body></html>"
    return noticeText


@app.route("/notice/<id>")
def notice(id):
    url = "http://www.nemweb.com.au/Reports/CURRENT/Market_Notice/" + id
    data = urllib.request.urlopen(url).read().decode('iso-8859-1','ignore')
    data = prettyNotice(data)
    
    return flask.Response(data, mimetype="text/html")

	
@app.route("/")
def index():
    return render_template('index.html')

	
@app.route("/dispatch")
def dispatch():
    s = session.query(dispatchIS).filter(dispatchIS.datetime > datetime.now() - timedelta(hours=48))
    export = {}
    for item in s:
         item = item.as_dict()
         if str(item['datetime']) not in export:
              export[str(item['datetime'])] = {}
         export[str(item['datetime'])][item['regionid']] = item
               
    return flask.jsonify(results=export)

	
if __name__ == "__main__":
    app.run(host='0.0.0.0')
