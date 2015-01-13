from flask import Flask, render_template 
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
#gm will hate me for this :P

#http://stackoverflow.com/questions/22315919/how-to-get-all-mysql-tuple-result-and-convert-to-json
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
    cnx = mysql.connector.connect(user=config['general']['dbuser'], password=config['general']['dbpassword'], database='nem')
    cnx.autocommit = True
    cursor = cnx.cursor()
    query = ("select * from dispatch_region_price_pivot order by datetime desc LIMIT 576")
    cursor.execute(query)
    a = dictfetchall(cursor)
    cursor.close()
    return flask.jsonify(results=a)

	
if __name__ == "__main__":
    app.run(host='0.0.0.0')
