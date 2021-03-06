from flask import render_template
from flask import Flask
from flask import request, session, redirect, url_for
import MySQLdb
import base64
import os
import random
import requests
import json
from flask import Flask,request,session
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
app = Flask(__name__)


a = 2 #a,b are curve parameters
b = 3
# functions for modular arithmetic operations


def mult(m,n):
	i = m
	r = 0
	for bi in range(128):
		if ( n & (1 << bi)):
			r = (r + i) % 263
		i = (i + i) % 263
	return r
    
def eea(m, n):
    assert(isinstance(m, int))
    assert(isinstance(n, int))
    (s, t, u, v) = (1, 0, 0, 1)
    while n != 0:
        (q, r) = (m // n, m % n)
        (unew, vnew) = (s, t)
        s = u - (q * s)
        t = v - (q * t)
        (m, n) = (n, r)
        (u, v) = (unew, vnew)
    (x, y, z) = (m, u, v)
    return (x, y, z)

def divi(m,n):
    x,y,z = eea(263,n)
    y = y % 263
    res = mult(m,y)
    return res

def exponent(i, j):
    n = i
    r = 1
    for bit in range(128):
        if (j & (1 << bit)):
            r = mult(r, n)
        n = mult(n, n)
    return r

# functions for point arithmetic on curve

def point_add(px,py,qx,qy):
    t1 = (py - qy) % 263
    t2 = (px - qx) % 263
    s = divi(t1,t2)
    resx = exponent(s,2) - px - qx
    resx = resx % 263
    t3 = (px - resx) % 263
    resy = (mult(s,t3) - py) % 263
    return (resx,resy)

def point_double(px,py):
    t1 = exponent(px,2)
    t2 = (mult(3,t1) + a) % 263
    t3 = mult(2,py)
    s = divi(t2,t3)
    resx = (exponent(s,2) - mult(2,px)) % 263
    t4 = (px-resx) % 263
    resy = (mult(s,t4) - py) % 263
    return (resx,resy)

def point_mult(k,px,py):
    nx = px
    ny = py
    resx = 0
    resy = 1
    cnt = 1
    for bit in range(128):
        if (k & (1 << bit)):
            if cnt == 1:
                resx,resy = nx,ny
                cnt+=1
            else:
                resx,resy = point_add(resx,resy,nx,ny)
        nx,ny = point_double(nx,ny)
    return (resx,resy)

def check_point(qx,qy):
    t1 = exponent(qy,2)
    t2 = (exponent(qx,3)+ mult(a,qx) + b) % 263
    return t1==t2

ntp = int(455)
f=int(455)

def validate_otp(var,count):
    global ntp
    if int(count) == 1:
        ntp = float(var)
        ans="1"
    else:
        inverse = float((2*float(var)-3-f)/3)
        #print("inverse is : {}".format(inverse))
        #print("otp is : {}".format(ntp))
        if inverse == ntp:
                ntp = var
                ans="1"
        else:
                ans="0"
    return ans





@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logchk', methods=['GET','POST'])
def logchk():
    if request.method == 'POST':
        if request.form['user'] == 'patient':
            #query frm patient table
            usrnm = request.form['um']
            conn = MySQLdb.connect(user="root", passwd="rishi26071997", db="rishi")
            cur = conn.cursor()
            cur.execute("select Pwd from Patient where userid = \""+usrnm+"\" ;")
            row = cur.fetchone()
            pwd = str(row[0])
            conn.commit()
            cur.close()
            conn.close()
            
            pwd_prvd = str(request.form['pass'])
            if (pwd==pwd_prvd):
                session['logged_in']= True
                session['username']=request.form['um']
                session['user']=request.form['user']
                return render_template('index.html')
            else:
                return render_template('login.html')
        elif request.form['user'] == 'doc':
            #query from doctor table
            
            usrnm = request.form['um']
            
            conn = MySQLdb.connect(user="root", passwd="rishi26071997", db="rishi")
            cur = conn.cursor()
            cur.execute("select Pwd from Credentials where userid = \""+usrnm+"\" ;")
            row = cur.fetchone()
            pwd = str(row[0])
            conn.commit()
            cur.close()
            conn.close()
            
            pwd_prvd = str(request.form['pass'])
            if (pwd==pwd_prvd):
                session['logged_in']= True
                session['username']=request.form['um']
                session['user']=request.form['user']
                return render_template('index.html')
            else:
                return render_template('login.html')

@app.route('/pat')
def pat():
    conn = MySQLdb.connect(user="root", passwd="rishi26071997", db="rishi")
    cur = conn.cursor()
    cur.execute("select userid from Patient;")
    row = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    #in this we will go to prescription page where doctor will assign some instruction for patient
    return render_template('patient.html',data=row)

@app.route('/assignpres')
def assignpres():

    #here prescription will got submitted and we will return to home page
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear();
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/crac', methods=['GET','POST'])
def crac():
    nm =request.form['um']
    pwd=request.form['pass']
    conn = MySQLdb.connect(user="root", passwd="rishi26071997", db="rishi")
    cur = conn.cursor()
    cur.execute("insert into Patient values (\""+nm+ "\""+",\""+pwd+"\");")
    conn.commit()
    cur.close()
    conn.close()    
    return render_template('login.html')


@app.route('/curvital')
def curvital():
    gx = 126 # gx,gy are the coordinates of the generator point
    gy = 76
    da = 2
    qax,qay = point_mult(da,gx,gy) # qax,qay are the public key coordinates
    
    count=1
    r1 = requests.post("http://127.0.0.1:5001/otp", data={'qax': qax, 'qay': qay , 'count':count})
    response=r1.text
    sx,sy = point_mult(3,qax,qay)
    s = str(sx) + str(sy)
    passkey = s.encode()
    salt = b'salt_'
    kdf = PBKDF2HMAC(
			         algorithm=hashes.SHA256(),
			         length=32,
			         salt=salt,
			         iterations=100000,
			         backend=default_backend()
			 )
			    
    key = base64.urlsafe_b64encode(kdf.derive(passkey))
    f1 = Fernet(key)
    msg = r1.text.encode()
    orig_msg = f1.decrypt(msg)
    print(orig_msg)
    ans = validate_otp(float(orig_msg),count)
    if ans == '1' :
            r1 = requests.post("http://127.0.0.1:5001/ecc", data={'qax': qax, 'qay': qay})
            sx,sy = point_mult(3,qax,qay)
            s = str(sx) + str(sy)
            passkey = s.encode()
            salt = b'salt_'
            kdf = PBKDF2HMAC(
			         algorithm=hashes.SHA256(),
			         length=32,
			         salt=salt,
			         iterations=100000,
			         backend=default_backend()
			 )
			    
            key = base64.urlsafe_b64encode(kdf.derive(passkey))
            f1 = Fernet(key)
            msg = r1.text.encode()
            orig_msg = f1.decrypt(msg)
            orig_msg = str(orig_msg.decode())
            t1,t2,t3,t4=orig_msg.split(':')
                
    else :
            print("otp not confirmed")
              
    return render_template('curvital.html',hb=t1,bt=t2,bp=t3,rr=t4) 
            
            
if __name__ == '__main__':
    app.secret_key = 'some secret key'
    app.run(host = "localhost" , port= 5000 ,threaded=True)