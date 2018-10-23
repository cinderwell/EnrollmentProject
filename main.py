__author__ = 'administrator'
import base64, string, datetime
import xmltodict
from pysimplesoap.client import SoapClient
from pysimplesoap.simplexml import SimpleXMLElement
from flask import Flask, render_template, request, Response, render_template, redirect, url_for, session, Session, flash, jsonify, json, app
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
import psycopg2
import os
import pymssql
import hashlib
from urllib import unquote
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import exceptions
from woocommerce import API
import json
from math import ceil
import locale
import bleach
from datetime import timedelta

locale.setlocale( locale.LC_ALL, '' )

c_key = '########'
c_secret = '########'


wcapi = API(
    url="https://www.fxw.org/",
    consumer_key=c_key,
    consumer_secret=c_secret,
    wp_api=True,
    version="wc/v2"
)

DEBUG = True
SECRET_KEY = '#######'
SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SERVER_NAME'] = 'enroll.fxw.org'
login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

veracross_auth_url = "##############"
veracross_base_url = "############"

login_manager.login_view = 'index'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

def clean_input(input):
    return bleach.clean(input)

def is_json(myjson):
  try:
    json_object = myjson.json()
  except ValueError, e:
    print "  no JSON response."
    return False
  return True

def getWeb(url):
    read_timeout = 10.0
    success = False
    retries = 0
    settings = {
    }
    while success == False:
        success = True
        try:
            r = requests.get(url, timeout=(1.0, read_timeout),
                                verify=False,
                                **settings)
            temp = r.json()
            #print temp
            if is_json(r):
                if "errors" in r.json():
                    print "   Attempted: "+url
                    print r.json()
                    success = False
        except requests.exceptions.ReadTimeout as e:
            print "   Attempted: "+url
            print "                      Read Timeout, waited too long between bytes."
            success = False
            retries += 1
        except requests.exceptions.SSLError as e:
            print "   Attempted: "+url
            print "                      SSL handshake timed out."
            success = False
            retries += 1
        except requests.exceptions.ConnectionError as e:
            print "   Attempted: "+url
            print "                      Connection Error, aborted by remote host?"
            success = False
            retries += 1
        except:
            print "   Attempted: "+url
            print "                       Uncaught error"
            if "<Response 200>" not in r:
                temp = "Critical Error: Please contact webmaster@fxw.org"
                success = True
            else:
                success = False
                retries += 1

    if retries > 0:
        print "                      success after "+str(retries+1)+" attempts"
    return temp

def postWeb(url):
    #Returns the user's PK if auth successful, or -1 if not
    read_timeout = 10.0
    success = False
    retries = 0
    output = -1
    put_settings = {

    }
    while success == False:
        success = True
        try:
            #print url
            r = requests.post(url, timeout=(1.0, read_timeout),
                                verify=False,
                                **put_settings)
            #print r
            res = xmltodict.parse(r.content)
            #print res
            '''
            temp = r.json()
            if is_json(r):
                if "errors" in r.json():
                    print "   Attempted: "+url
                    print r.json()
                    success = False
                    if "The specified resource does not exist." in r.json()['errors'][0]['message']:
                        success = True
            '''
        except requests.exceptions.ReadTimeout as e:
            print "   Attempted: "+url
            print "                      Read Timeout, waited too long between bytes."
            success = False
            retries += 1
        except requests.exceptions.SSLError as e:
            print "   Attempted: "+url
            print "                      SSL handshake timed out."
            success = False
            retries += 1
        except requests.exceptions.ConnectionError as e:
            print "   Attempted: "+url
            print "                      Connection Error, aborted by remote host?"
            success = False
            retries += 1
        #except:
        #    print "   Attempted: "+url
        #    print "                       Uncaught error"
        #    success = False
        #    retries += 1

    if retries > 0:
        print "                      success after "+str(retries+1)+" attempts"

    try:
        output = res['auth']['person_pk']
    except:
        output = -1

    return output

def getSisID(username):
    ee_user = '###########'
    ee_pass = '###########'
    server = '###########'
    conn = pymssql.connect(server, ee_user, ee_pass, 'FE')
    cursor = conn.cursor()
    payload = """SELECT [EA7RECORDSID]
    ,[ONLINEUSERID]
    ,[ONLINEPASSWORD]
    ,[USERDEFINEDID]
    ,[BBNC_ClientUsersID]
    FROM [FE].[dbo].[EA7RECORDS]
    where ONLINEUSERID='"""+str(username)+"""'"""
    try:
        cursor.execute(payload)
        row = cursor.fetchone()
        return row[3] #actual column?
    except:
        print "I am unable to connect to the database"
        logEvent('getSisID',payload,'Database connection error')
        return None

def getID(username):
    nc_user = '########'
    nc_pass = '##########'
    server = '############'
    conn = pymssql.connect(server, nc_user, nc_pass, 'BBNC')
    cursor = conn.cursor()
    payload = """SELECT *
     FROM [BBNC].[dbo].[ClientUsers]
     where UserName='"""+str(username)+"""'"""
    try:
        cursor.execute(payload)
        row = cursor.fetchone()
        return row[0] #actual column?
    except:
        print "I am unable to connect to the database"
        logEvent('getID',payload,'Database connection error')
        return None

def getUsername(id):
    nc_user = '########'
    nc_pass = '##########'
    server = '############'
    conn = pymssql.connect(server, nc_user, nc_pass, 'BBNC')
    cursor = conn.cursor()
    payload = """SELECT UserName
     FROM [BBNC].[dbo].[ClientUsers]
     where ID='"""+str(id)+"""'"""
    try:
        cursor.execute(payload)
        row = cursor.fetchone()
        return row[0] #actual column?
    except:
        print "I am unable to connect to the database"
        logEvent('getUsername',payload,'Database connection error')
        return None
#print getSisID('MitchellD@fxw.org')
#print getUsername(4595)


class UserNotFoundError(Exception):
    pass

#Because we're using SSO, this just caches a list of logins
class User(UserMixin):
#class User():
    USERS = {
        # username: password
        #'john': 'love mary',
        #'mary': 'love peter'
    }
    SIS_IDS = {
        # username: sis_id
    }

    def __init__(self,id): #self,id
        if not id in self.USERS:
            #raise UserNotFoundError()
            self.USERS.update({id: ''})
        self.id = id
        self.password = self.USERS[id]

        #self.sis_id = sis_id #self.SIS_IDS[id]
        self.sis_id = self.SIS_IDS[id]
        #self.sis_id = 0
        #print id

    @classmethod
    def get(self_class, id):
        '''Return user instance of id, return None if not exist'''
        try:
            return self_class(id)
        except UserNotFoundError:
            return None

    def get_sis_id(self):
        try:
            return unicode(self.sis_id)
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')

    def set_sis_id(self,sis_id):
        self.sis_id = unicode(sis_id)
        self.SIS_IDS.update({id: sis_id})


    @classmethod
    def add_sis_id(self_class,id,sis_id):
        self_class.SIS_IDS.update({id: sis_id})




class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.String)
    #remove user_id when we cutover to a different auth system
    #user_id = db.Column(db.Integer)
    username = db.Column(db.String)
    action = db.Column(db.String)
    post = db.Column(db.Text)
    response = db.Column(db.Text)

class Logins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.String)
    username = db.Column(db.String)
    status = db.Column(db.String)

class Signatures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.String)
    form = db.Column(db.String)
    username = db.Column(db.String)
    signature = db.Column(db.String)

db.create_all()


@app.before_first_request
def init_request():
    db.create_all()

def logEvent(action,post,response):
    #id won't be important if we stop using a local db to auth
    id = current_user.get_id()
    log = Log(created=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),username=id,action=action,post=post,response=response)
    db.session.add(log)
    db.session.commit()
    return None

def logLogin(username,status):
    logins = Logins(created=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),username=username,status=status)
    db.session.add(logins)
    db.session.commit()
    return None

def logSignature(username,form,signature):
    sig = Signatures(created=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),username=username,form=form,signature=signature)
    db.session.add(sig)
    db.session.commit()
    return None

def getStudents(sis_id):
    payload = """
        select bp.c_bpartner_id as parent_id, bp.value as parent_sis_id, bp.name, rel.relationship,
        rel.relationship_reciprocal, rel.relative as relative_id, stu.value, stu.name
        from public.sf_relative rel
        inner join c_bpartner bp on rel.c_bpartner_id=bp.c_bpartner_id
        inner join c_bpartner stu on rel.relative=stu.c_bpartner_id
        where rel.isactive='Y'
        and bp.isactive='Y'
        and stu.isactive='Y'
        and bp.value='"""+str(sis_id)+"""'
        and bp.ad_client_id='__________'
        order by stu.created desc"""
    try:
        conn = psycopg2.connect("dbname='openbravo' user='postgres' host='_________' password='_________'")
        cur = conn.cursor()
        cur.execute(payload)
        #logEvent('getStudents',payload,'Database connection error')
        rows = cur.fetchall()

        '''
        for row in rows:
            output = ""
            for col in row:
                output+="  "+str(col)
            print output
        '''
        return rows
    except:
        print "I am unable to connect to the database"
        logEvent('getStudents',payload,'Database connection error')
        return None

def getStudentPay(partner_id):
    #print partner_id
    '''
    payload = """
        select ap.c_bpartner_id, ap.c_bpartner_parent, ap.epcs_c_bpartner_epayment_id, ap.pay_rules, ap.payment_date, ap.fixed_amount, ap.fin_paymentmethod_id, ap.isactive
        from sfa_autopay ap
        inner join c_bpartner bp on ap.c_bpartner_id=bp.c_bpartner_id
        where ap.c_bpartner_id='"""+str(partner_id)+"""'
        and ap.isactive='Y'"""
    '''
    payload = """select ap.c_bpartner_id, ap.c_bpartner_parent, ap.epcs_c_bpartner_epayment_id, ap.pay_rules, ap.payment_date, ap.fixed_amount, ap.fin_paymentmethod_id
      from sfa_autopay ap
      inner join c_bpartner bp on ap.c_bpartner_id=bp.c_bpartner_id
      where ap.c_bpartner_id='"""+str(partner_id)+"""'
      and ap.isactive='Y'"""
    try:
        conn = psycopg2.connect("dbname='openbravo' user='postgres' host='_________' password='_________'")
        cur = conn.cursor()
        cur.execute(payload)
        rows = cur.fetchall()
        '''
        for row in rows:
            output = ""
            for col in row:
                output+="  "+str(col)
            print output
        '''

        return rows
    except:
        print "I am unable to connect to the database"
        logEvent('getStudents',payload,'Database connection error')
        return None

def getPayInfo(payment_id):
    '''
    payload = """
        select ps.epcs_c_bpartner_epayment_id, ps.epcs_type, ps.accountnumber, ps.isdefault, ps.epcs_status, bp.value, bp.name
        from epcs_c_bpartner_epayment ps
        inner join c_bpartner bp on ps.c_bpartner_id=bp.c_bpartner_id
        where ps.c_bpartner_id='"""+str(payment_id)+"""'"""
    '''
    payload = """select ps.epcs_c_bpartner_epayment_id, ps.epcs_type, ps.accountnumber, ps.isdefault, ps.epcs_status, bp.value, bp.name
      from epcs_c_bpartner_epayment ps
      inner join c_bpartner bp on ps.c_bpartner_id=bp.c_bpartner_id
      where ps.epcs_c_bpartner_epayment_id='"""+str(payment_id)+"""'"""
    try:
        conn = psycopg2.connect("dbname='openbravo' user='postgres' host='_________' password='_________'")
        cur = conn.cursor()
        cur.execute(payload)
        rows = cur.fetchall()
        '''
        for row in rows:
            output = ""
            for col in row:
                output+="  "+str(col)
            print output
        '''

        return rows
    except:
        print "I am unable to connect to the database"
        logEvent('getPayInfo',payload,'Database connection error')
        return None

def getPayMethods(partner_id):
    payload = """
        select ps.epcs_c_bpartner_epayment_id, ps.subsctiption, ps.epcs_type, ps.accountnumber, ps.isdefault, ps.epcs_status
        from c_bpartner bp
        inner join epcs_c_bpartner_epayment ps on ps.c_bpartner_id=bp.c_bpartner_id
        where bp.value='"""+str(partner_id)+"""'"""
    try:
        conn = psycopg2.connect("dbname='openbravo' user='postgres' host='_________' password='_________'")
        cur = conn.cursor()
        #print partner_id
        cur.execute(payload)
        rows = cur.fetchall()
        '''
        for row in rows:
            output = ""
            for col in row:
                output+="  "+str(col)
            print output
        '''

        return rows
    except:
        print "I am unable to connect to the database"
        logEvent('getPayMethods',payload,'Database connection error')
        return None

username = "___________"
password = "___________"
base_url = "___________"
headers = {'content-type': 'application/soap+xml'}

settings = {
    "headers": {
    }
}

def getXml(url, settings, body):
    read_timeout = 240.0
    success = False
    retries = 0
    #print url
    #print body
    while success == False:
        success = True
        try:
            #r = requests.get(url+woo_url2, timeout=(1.0, read_timeout), verify=True)
            #print url+woo_url2

            #r = requests.get(url, timeout=(1.0, read_timeout), verify=True,allow_redirects=False,**settings2)
            '''
            settings['headers'].update({
              "Content-Length": len(body)
            })
            '''

            r = requests.post(
              url,
              timeout=(1.0, read_timeout),
              data=body,
              verify=True,
              auth=(username,password),
              allow_redirects=False,
              **settings)
            
        except requests.exceptions.ReadTimeout as e:
            print "                      Read Timeout, waited too long between bytes."
            logEvent('getXML',body,'Read Timeout, waited too long between bytes')
            success = False
            retries += 1
        except requests.exceptions.SSLError as e:
            print "                      SSL handshake timed out."
            logEvent('getXML',body,'SSL handshake timed out')
            success = False
            retries += 1
        except requests.exceptions.ConnectionError as e:
            print "                      Connection Error, aborted by remote host?"
            logEvent('getXML',body,'Connection Error, aborted by remote host?')
            success = False
            retries += 1
    if retries > 0:
        print "                      success after "+str(retries+1)+" attempts"
        logEvent('getXML',body,"success after "+str(retries+1)+" attempts")
    return r


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

'''
def get_sis_id():
    user = current_user.get_id()
    if 'sis_id' not in session:
        session['sis_id'] =
    return session['sis_id']
'''
def check_auth(username,password):
    #force lower-case
    username = username.lower()
    '''
    user = User.query.filter_by(username=username).filter_by(password=password)
    if user.count() == 1:
        return True
    else:
        return False
    '''
    user_pk = postWeb(veracross_auth_url+"?username="+str(username)+"&password="+str(password))
    if user_pk == -1:
        return False
    else:
        return True

def valid_amount(amount):
    try:
        number = float(amount)
        if number > 0.0:
            return True
        else:
            return False
    except ValueError:
        return False
    return True

def check_hash(username,hash):
    #systemID = getSystemID(username)

    #going to need to redesign this to talk to netcommunity directly
    username = username.lower()
    #don't lowercase the username, then test against netcommunity and pull out sis_id, system id, and username
    user = User.query.filter_by(username=username)
    if user.count() != 0:
        password = user[0].password
        string_to_hash = username+password
        correct_hash = hashlib.sha256(string_to_hash).hexdigest()
        #if hash == correct_hash:
        #   create the user temporarily(username,sis_id,system id)
        #   return True
        #else:
        #   return False
        return hash == correct_hash
    else:
        return False

def strip_errors(error):
    error = string.replace(error,"""<html><head><title>Apache Tomcat/6.0.35 - Error report</title><style><!--H1 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:22px;} H2 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:16px;} H3 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:14px;} BODY {font-family:Tahoma,Arial,sans-serif;color:black;background-color:white;} B {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;} P {font-family:Tahoma,Arial,sans-serif;background:white;color:black;font-size:12px;}A {color : black;}A.name {color : black;}HR {color : #525D76;}--></style> </head>""",'')
    error = string.replace(error,'<html>','')
    error = string.replace(error,'</html>','')
    error = string.replace(error,'<body>','')
    error = string.replace(error,'</body>','')
    error = string.replace(error,"""<HR size="1" noshade="noshade">""",'')
    error = string.replace(error,"""<hr size="1" noshade="noshade">""",'')
    error = string.replace(error,"""<h3>Apache Tomcat/6.0.35</h3>""",'')
    error = string.replace(error,"""<h1>""",'')
    error = string.replace(error,"""</h1>""",'')
    error = string.replace(error,"""<p>""",'<br>')
    error = string.replace(error,"""</p>""",'')
    error = string.replace(error,"""<u>""",'')
    error = string.replace(error,"""</u>""",'')
    error = string.replace(error,"""HTTP Status 400 - """,'')
    return error

@app.route('/logout')
def logout():
    session.pop('students', None)
    session.pop('cart', None)
    logout_user()
    return redirect('https://portals.veracross.com/fxw/')

@app.route("/home")
@login_required
def home():
    hasPayMethods = False

    status=None
    if request.args.get('success'):
        if request.args.get('success') == 'true':
            status = "Successfully updated payment method."
    user = current_user.get_id()

    sis_id = current_user.get_sis_id()
    #sis_id = '25'

    data2 = getPayMethods(sis_id)
    if data2:
        hasPayMethods = True
    data = getStudents(sis_id)
    students = []
    if data:
        for counter,row in enumerate(data):
            students.append({})
            students[counter]['partner_id'] = row[5]
            students[counter]['sis_id'] = row[6]
            students[counter]['name'] = row[7]
            students[counter]['pay_type'] = None
            students[counter]['card_num'] = None
            students[counter]['card_name'] = None
            students[counter]['pay_date'] = None
            pay_id = getStudentPay(students[counter]['partner_id'])
            if pay_id:
                students[counter]['pay_date'] = pay_id[0][4]
                pay_info = getPayInfo(pay_id[0][2])
                #print pay_info
                students[counter]['pay_type'] = pay_info[0][1]
                if students[counter]['pay_type'] == '001':
                    students[counter]['pay_type'] = "Visa"
                if students[counter]['pay_type'] == '002':
                    students[counter]['pay_type'] = "Master Card"
                if students[counter]['pay_type'] == '003':
                    students[counter]['pay_type'] = "American Express"
                if students[counter]['pay_type'] == '004':
                    students[counter]['pay_type'] = "Discover"
                students[counter]['card_num'] = pay_info[0][2]
                students[counter]['card_name'] = pay_info[0][6]
    return render_template('home.html', user=user, students=students, status=status, hasPayMethods=hasPayMethods)

@app.route("/terms")
@login_required
def terms():
    user = current_user.get_id()
    sis_id = current_user.get_sis_id()
    return render_template('terms.html', user=user)

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    url = "________"
    error = None
    selected_student = None
    if request.args.get('id'):
        selected_student = request.args.get('id')

    user = current_user.get_id()
    sis_id = current_user.get_sis_id()

    data = getStudents(sis_id)
    students = []

    if data:
        for counter,row in enumerate(data):
            students.append({})
            students[counter]['partner_id'] = row[5]
            students[counter]['sis_id'] = row[6]
            students[counter]['name'] = row[7]

    if request.method == 'POST':
        #print "posted"
        checked_students = request.form.getlist("checked_students")
        #print checked_students
        #print len(checked_students)
        pay_method = request.form["pay_method"]
        #print pay_method
        #print checked_students
        accepted = request.form.getlist("accept")
        if bool(accepted) and request.form["eSig"]:
            if(len(checked_students) < 1):
                error = "No students selected."
            else:
                if pay_method == "VISA" or pay_method == "MASTERCARD" or pay_method == "AMERICANEXPRESS":
                    body = """<?xml version="1.0" encoding="UTF-8"?>
                    <Enrollment>
                    <Parent>
                        <ParentID>"""+sis_id+"""</ParentID>
                        <Account>
                            <GenerateAccount>Y</GenerateAccount>
                            <IsCreditCard>Y</IsCreditCard>
                            <AccountType>"""+str(pay_method)+"""</AccountType>
                            <AccountNumber>"""+str(request.form["card_num"])+"""</AccountNumber>
                            <CreditCardYear>"""+str(request.form["card_year"])+"""</CreditCardYear>
                            <CreditCardMonth>"""+str(request.form["card_month"])+"""</CreditCardMonth>
                            <CreditCardCVN>"""+str(request.form["card_cvv"])+"""</CreditCardCVN>
                            <AccountAddress>"""+str(request.form["address"])+"""</AccountAddress>
                            <AccountPostalCode>"""+str(request.form["zip"])+"""</AccountPostalCode>
                            <AccountCity>"""+str(request.form["city"])+"""</AccountCity>
                            <AccountRegion>"""+str(request.form["state"])+"""</AccountRegion>
                            <AccountCountry>United States</AccountCountry>
                            <AccountEmail>"""+str(request.form["email"])+"""</AccountEmail>
                        </Account>
                    </Parent>
                    </Enrollment>"""
                else:
                    #print str(request.form["account_phone"])
                    driver_id = str(request.form["driver_id"])
                    driver_id = string.replace(driver_id,' ','')
                    driver_id = string.replace(driver_id,'-','')
                    driver_id = string.replace(driver_id,'.','')
                    account_phone = str(request.form["account_phone"])
                    account_phone = string.replace(account_phone,'(','')
                    account_phone = string.replace(account_phone,')','')
                    account_phone = string.replace(account_phone,'-','')
                    account_phone = string.replace(account_phone,' ','')
                    #print str(driver_id)
                    body = """<?xml version="1.0" encoding="UTF-8"?>
                    <Enrollment>
                    <Parent>
                        <ParentID>"""+sis_id+"""</ParentID>
                        <Account>
                            <GenerateAccount>Y</GenerateAccount>
                             <IsCreditCard>N</IsCreditCard>
                             <AccountType>"""+str(pay_method)+"""</AccountType>
                            <AccountNumber>"""+str(request.form["account_num"])+"""</AccountNumber>
                            <AccountAddress>"""+str(request.form["address"])+"""</AccountAddress>
                            <AccountPostalCode>"""+str(request.form["zip"])+"""</AccountPostalCode>
                            <AccountCity>"""+str(request.form["city"])+"""</AccountCity>
                            <AccountRegion>"""+str(request.form["state"])+"""</AccountRegion>
                            <AccountCountry>United States</AccountCountry>
                            <AccountEmail>"""+str(request.form["email"])+"""</AccountEmail>
                            <AccountPhoneNumber>"""+str(account_phone)+"""</AccountPhoneNumber>
                            <AccountTransitNumber>"""+str(request.form["routing_num"])+"""</AccountTransitNumber>
                            <AccountDriverLicenceNo>"""+str(driver_id)+"""</AccountDriverLicenceNo>
                            <AccountDriverLicenceState>"""+str(request.form["driver_id_state"])+"""</AccountDriverLicenceState>
                        </Account>
                    </Parent>
                    </Enrollment>"""

                settings = {
                    "headers": {
                    }
                }
                #print body
                response = getXml(url,settings,body)
                #print response.text
                if response.status_code == 200:
                    result = xmltodict.parse(response.text)
                    token = result['Response']['Parent']['TokenID']
                    pay_date = request.form["pay_date"]
                    #print token
                    #print str(pay_date)
                    error = ""
                    #Begin looping through selected students and applying the payment token to them here
                    #for id in checked_students:
                    for id in checked_students:
                        body2 = """<?xml version="1.0" encoding="UTF-8"?>
                        <Enrollment>
                        <Student>
                            <TokenID>"""+str(token)+"""</TokenID>
                            <ParentID>"""+sis_id+"""</ParentID>
                            <PaymentDate>"""+str(pay_date)+"""</PaymentDate>
                            <StudentID>"""+str(id)+"""</StudentID>
                        </Student>
                        </Enrollment>"""
                        response2 = getXml(url,settings,body2)
                        #print response2.text
                        if response2.status_code == 400:
                            error+=strip_errors(response.text)
                            error+='<br>'
                    if error == "":
                        logSignature(user,"Add Form",request.form["eSig"])
                        return redirect(url_for('home',success='true'))

                if response.status_code == 400:
                    error=response.text
                    error = strip_errors(error)
                    #print error
                    #logEvent('Add Payment Method API',body,str(error))
        else:
            error = "You must accept the terms and agreements, and sign."
    return render_template('add.html', user=user, students=students, selected_student=selected_student, error=error)

@app.route('/store', methods=['GET'])
@login_required
def store():
    user = current_user.get_id()
    data = session['students']
    #print session['cart']
    cart_size = len(session['cart'])
    '''
    student_names = []
    student_ids = []
    if students:
        for student in students:
            student_names.append(student[7])
            student_ids.append(student[6])
    print student_names
    print student_ids

    print students
    '''
    students = []
    if data:
        for counter,row in enumerate(data):
            students.append({})
            students[counter]['sis_id'] = row[6]
            students[counter]['name'] = row[7]


    return render_template('store.html',user=user,students=students,cart_size=cart_size)

@app.route('/select', methods=['GET','POST'])
@login_required
def select():
    user = current_user.get_id()
    sis_id = current_user.get_sis_id()
    data = session['students']
    sku = ""
    error = ""
    sku = request.args.get('sku', '')
    message = ""
    
    product_name = ""
    price = ""
    years = []
    variable_price = False
    edp_options = False
    if sku == 'BUS0043':
        price = "500.00"
        product_name = "7:40 AM Bus OSP to HNC"
        product_id = 738
        years.append('2017-2018')
    elif sku == 'BUS0040':
        price = "500.00"
        product_name = "3:10 PM Bus OSP to HNC"
        product_id = 740
        years.append('2017-2018')
    elif sku == 'BUS0041':
        price = "500.00"
        product_name = "3:40 PM Bus HNC to OSP"
        product_id = 741
        years.append('2017-2018')
    elif sku == 'BUS0042':
        price = "500.00"
        product_name = "4:30 PM Bus OSP to HNC"
        product_id = 742
        years.append('2017-2018')
    elif sku == 'BUS0051':
        price = "500.00"
        product_name = "5:00 PM Bus HNC to OSP"
        product_id = 1021
        years.append('2017-2018')
    elif sku == 'BUS0050':
        price = "500.00"
        product_name = "5:30 PM Bus OSP to HNC"
        product_id = 1020
        years.append('2017-2018')
    elif sku == 'MF0070':
        price = "30.00"
        product_name = "Extended Day Late Fee"
        product_id = 722
        years.append('2017-2018')
    elif sku == 'EC0050':
        price = "200.00"
        product_name = "Extended Day Registration"
        product_id = 734
        edp_options = True
        years.append('2017-2018')
    elif sku == "TUI-01":
        product_id = 721
        variable_price = True
        years.append('2017-2018')
        years.append('2016-2017')
        years.append('2015-2016')
        years.append('2014-2015')
        years.append('2013-2014')
        years.append('2012-2013')
        years.append('2011-2012')
        product_name = "Tuition Payment"
    else:
        return redirect(url_for('store'))

    students = []
    if data:
        for counter,row in enumerate(data):
            students.append({})
            students[counter]['sis_id'] = row[6]
            students[counter]['name'] = row[7]

    if request.method == 'POST':
        if sku == "TUI-01":
            checked_students = request.form.getlist("checked_students")
            if(len(checked_students) < 1):
                error = "No students selected."
            elif(valid_amount(request.form['amount']) == False):
                error = "Invalid amount."
            else:
                #session['cart'].append()
                item = {}
                item['amount'] = float(clean_input(request.form['amount']))
                item['display_amount'] = locale.currency(float(clean_input(request.form['amount'])), grouping=True)
                item['parent_id'] = sis_id
                item['student_id'] = request.form.getlist("checked_students")
                item['sku'] = sku
                item['product_id'] = product_id
                item['name'] = product_name
                item['year'] = request.form['year']
                session['cart'].append(item)
                return redirect(url_for('store'))
        else:
            if request.form['stu']:
                item = {}
                item['amount'] = float(price)
                item['display_amount'] = locale.currency(float(price), grouping=True)
                item['parent_id'] = sis_id
                item['student_id'] = request.form['stu']
                item['sku'] = sku
                item['product_id'] = product_id
                if edp_options == True:
                    item['name'] = str(product_name)+": "+request.form['edp']
                else:
                    item['name'] = product_name
                item['year'] = request.form['year']
                session['cart'].append(item)
                return redirect(url_for('store'))
            else:
                error = "No student selected."

    return render_template('select.html',user=user,students=students,sku=sku,price=price,product_name=product_name,years=years,variable_price=variable_price,edp_options=edp_options,error=error,message=message)

@app.route('/cart', methods=['GET','POST'])
@login_required
def cart():
    user = current_user.get_id()
    sis_id = current_user.get_sis_id()
    data = session['students']
    total = 0
    students = {}
    if data:
        for counter,row in enumerate(data):
            students[row[6]] = row[7]
    #print students

    cart_contents = []
    cart_id = 0
    if session['cart']:
        for item in session['cart']:
            total += float(item['amount'])
            item['cart_id'] = cart_id
            cart_id = cart_id+1
            if item['sku'] == "TUI-01":
                item['student_name'] = ""
                for i, stu_id in enumerate(item['student_id']):
                    if i==0:
                        item['student_name']+=(students[stu_id])
                    else:
                        item['student_name']+=", "
                        item['student_name']+=(students[stu_id])
            else:
                item['student_name'] = students[item['student_id']]
            cart_contents.append(item)
                #cart_contents[counter]['name'] = row[7]
        #print cart_contents

    total = locale.currency(total, grouping=True )

    if request.method == 'POST':
        to_delete = int(request.form['btn'])
        try:
            session['cart'].pop(to_delete)
        except:
            nothing = 0
        return redirect(url_for('cart'))

    return render_template('cart.html',user=user,cart_contents=cart_contents,total=total)

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    user = current_user.get_id()
    sis_id = current_user.get_sis_id()
    data = session['students']
    total = 0
    error = ""
    students = {}
    if data:
        for counter,row in enumerate(data):
            students[row[6]] = row[7]
    #print students

    cart_contents = []
    cart_id = 0
    if session['cart']:
        for item in session['cart']:
            total += float(item['amount'])
            item['cart_id'] = cart_id
            cart_id = cart_id+1
            if item['sku'] == "TUI-01":
                item['student_name'] = ""
                for i, stu_id in enumerate(item['student_id']):
                    if i==0:
                        item['student_name']+=(students[stu_id])
                    else:
                        item['student_name']+=", "
                        item['student_name']+=(students[stu_id])
            else:
                item['student_name'] = students[item['student_id']]
            cart_contents.append(item)
                #cart_contents[counter]['name'] = row[7]
        #print cart_contents

        total = locale.currency(total, grouping=True )

        if request.method == 'POST' and session['cart']:
            temp_first_name = clean_input(request.form['first_name'])
            temp_last_name = clean_input(request.form['last_name'])
            temp_address1 = clean_input(request.form['address1'])
            temp_address2 = clean_input(request.form['address2'])
            temp_city = clean_input(request.form['city'])
            temp_state = clean_input(request.form['state'])
            temp_zip_code = clean_input(request.form['zip_code'])
            temp_phone_num = clean_input(request.form['account_phone'])
            temp_email = clean_input(request.form['email'])
            '''
            print temp_first_name
            print temp_last_name
            print temp_address1
            print temp_address2
            print temp_city
            print temp_state
            print temp_zip_code
            print temp_phone_num
            '''
            data = session['students']
            students = {}
            if data:
                for counter,row in enumerate(data):
                    students[row[6]] = row[7]


            temp_line_items = []
            i = 0
            for item in session['cart']:
                if i > 0:
                    temp_line_items+=','
                temp_sku = item['sku']
                temp_product_id = item['product_id']
                temp_price = item['amount']
                temp_display_price = item['display_amount']
                temp_product_name = item['name']
                temp_year = item['year']
                temp_meta_data = []
                temp_meta_data.append({"value": temp_year, "id": 140, "key": "Academic Year"})
                temp_meta_data.append({"value": temp_display_price, "id": 300, "key": "Amount"})

                if temp_sku == 'TUI-01':
                    temp_parent_id = item['parent_id']
                    temp_meta_data.append({"value": temp_parent_id, "id": 142, "key": "Parent ID"})
                    j = 0
                    for stu in item['student_id']:
                        j+=1
                        temp_student_id = stu
                        temp_append = {"value": temp_student_id, "id": 143+j, "key": "Student ID"+str(j)}
                        temp_meta_data.append(temp_append)
                        temp_append = {"value": students[str(temp_student_id)], "id": 243+j, "key": "Student Name"+str(j)}
                        temp_meta_data.append(temp_append)
                else:
                    temp_student_id = item['student_id']
                    temp_parent_id = item['parent_id']
                    #temp_meta_data+=','
                    #temp_meta_data+=str({"value": temp_student_id, "id": 141, "key": "Student ID"})
                    #temp_meta_data+=','
                    #temp_meta_data+=str({"value": temp_parent_id, "id": 142, "key": "Parent ID"})
                    temp_meta_data.append({"value": temp_student_id, "id": 141, "key": "Student ID"})
                    temp_meta_data.append({"value": temp_parent_id, "id": 142, "key": "Parent ID"})
                    temp_meta_data.append({"value": students[temp_student_id], "id": 143, "key": "Student Name"})

                temp_line_items.append({"sku": str(temp_sku), "total_tax": "0.00", "product_id": str(temp_product_id), "quantity": 1, "total": str(temp_price), "subtotal": str(temp_price), "price": str(temp_price), "tax_class": 0, "variation_id": 0, "taxes": [], "name": str(temp_product_name),
        "meta_data": temp_meta_data
         })
                i+=1

            payload = {
            "payment_method": "cybersource_sa_sop_echeck",
            "payment_method_title": "eCheck",
            "set_paid": False,
            "billing": {
                "first_name": str(temp_first_name),
                "last_name": str(temp_last_name),
                "address_1": str(temp_address1),
                "address_2": str(temp_address2),
                "city": str(temp_city),
                "state": str(temp_state),
                "postcode": str(temp_zip_code),
                "country": "US",
                "email": str(temp_email),
                "phone": str(temp_phone_num)
            },
            "shipping": {},
            "line_items": temp_line_items
            ,
            "shipping_lines": [],

            }
            temp = payload
            #print json.dumps(temp)
            #print payload

            temp = wcapi.post("orders", payload)
            temp = temp.json()
            if('id' in temp and 'order_key' in temp):
                order_id = temp['id']
                order_key = temp['order_key']
                checkout_url = 'https://www.fxw.org/checkout/order-pay/'+str(order_id)+'/?pay_for_order=true&key='+str(order_key)
                return redirect(checkout_url)
            else:
                try:
                    error = json.dumps(temp)
                    print json.dumps(temp)
                except:
                    error = "Unknown"
                return redirect(url_for('checkout'))

            #return redirect(url_for('checkout'))
    return render_template('checkout.html',user=user,cart_contents=cart_contents,total=total,error=error)

@app.route('/change', methods=['GET', 'POST'])
@login_required
def change():
    error = ""
    url = "______________"
    id = current_user.get_id()
    #result = User.query.filter_by(id=id)
    #user = result[0].username
    #sis_id = result[0].sis_id
    user = current_user.get_id()
    sis_id = current_user.get_sis_id()

    data = getPayMethods(sis_id)
    student_name = ""
    pay_methods = []

    if data:
        for counter,row in enumerate(data):
            pay_methods.append({})
            pay_methods[counter]['name'] = row[2]
            if pay_methods[counter]['name'] == '001':
                pay_methods[counter]['name'] = "Visa"
            if pay_methods[counter]['name'] == '002':
                pay_methods[counter]['name'] = "Master Card"
            if pay_methods[counter]['name'] == '003':
                pay_methods[counter]['name'] = "American Express"
            if pay_methods[counter]['name'] == '004':
                pay_methods[counter]['name'] = "Discover"
            pay_methods[counter]['token'] = row[1]
            pay_methods[counter]['account'] = row[3]
    #print pay_methods
    if request.args.get('id'):
        selected_student = request.args.get('id')
        data2 = getStudents(sis_id)
        students = []
        if data2:
            for counter,row in enumerate(data2):
                if selected_student == row[6]:
                    student_name = row[7]

    else:
        #if we don't have a student already selected to change, send them home
        return redirect(url_for('home'))

    if request.method == 'POST':
        #print "posting"
        token = None
        pay_date = None
        accepted = request.form.getlist("accept")
        if bool(accepted) and request.form["eSig"]:
            if request.form["pMethod"]:
                token = request.form["pMethod"]
            if request.form["pay_date"]:
                pay_date = request.form["pay_date"]
            if token and pay_date:
                body = """<?xml version="1.0" encoding="UTF-8"?>
                <Enrollment>
                <Student>
                <TokenID>"""+str(token)+"""</TokenID>
                <ParentID>"""+sis_id+"""</ParentID>
                <PaymentDate>"""+str(pay_date)+"""</PaymentDate>
                <StudentID>"""+str(selected_student)+"""</StudentID>
                </Student>
                </Enrollment>"""
                response = getXml(url,settings,body)
                print response.text
                if response.status_code == 400:
                    error=strip_errors(response.text)
                if error == "":
                    logSignature(user,"Change Form",request.form["eSig"])
                    return redirect(url_for('home',success='true'))
            else:
                error = "Invalid payment method or date."
        else:
            error = "You must accept the terms and agreements, and sign."
    return render_template('change.html', error=error,pay_methods=pay_methods,student_name=student_name,user=user)

@app.route('/whois')
def whois():
    #print "recieved request"
    user_string = request.args.get('user')
    #print user_string
    if user_string:
        user_par = unquote(request.args.get('user'))
        user_id = getID(user_par)
        js = jsonify({'user_id': user_id})
        if user_id:
            return js
        else:
            return jsonify({'user_id': 'Unknown'})
    else:
        return jsonify({'user_id': 'Unknown'})


@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    #redirect to home if already logged in
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('home'))
    #login
    if request.method == 'POST':
        temp_username = clean_input(request.form['username'])
        temp_password = clean_input(request.form['password'])
        #user_pk = postWeb(veracross_auth_url+"?username="+str(request.form['username'])+"&password="+str(request.form['password']))
        user_pk = postWeb(veracross_auth_url+"?username="+str(temp_username)+"&password="+str(temp_password))
        #if not check_auth(request.form['username'], request.form['password']):
        if user_pk < 0:
            #user_par = request.form['username'].lower()
            #user_par = temp_username.lower()
            username = temp_username.lower()
            user_par = username
            logLogin(user_par,"invalid login")
            error = 'Invalid Credentials. Please try again.'
        else:
            #user_par = request.form['username'].lower()
            #username = request.form['username'].lower()
            username = temp_username.lower()
            user_par = username
            if(username):
                User.add_sis_id(username,user_pk)
                user = User(username)
                login_user(user)
                #user.set_sis_id(int(user_pk))
                logLogin(username,'success')
                session['students'] = getStudents(user_pk)
                session['cart'] = []
            #user = User.query.filter_by(username=user_par).filter_by(password=request.form['password'])
            #login_user(user.one())
            #logLogin(user_par,"login success")
            return redirect(url_for('home'))
    return render_template('index.html', error=error)



if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    host = os.getenv('IP', '0.0.0.0')
    host='enroll.fxw.org'
    app.run(port=port, host=host)
