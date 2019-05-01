import base64
import os
import random
import serial
import time
import requests
from flask import Flask,request,session
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

ard = serial.Serial('COM7',9600)
time.sleep(2)
a = 2 #a,b are curve parameters
b = 3
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

gx = 126
gy = 76
f=455
temp1=9


app = Flask(__name__)


@app.route("/otp",methods=['POST'])
def hello2():
    global temp1
    qax = request.form['qax']
    qay = request.form['qay']
    count = request.form['count']
    if count=='1':
            temp1 = 9
            temp1 = (3 * temp1 + f + 3)/2
    else:
            temp1 = (3 * temp1 + f + 3)/2
    qax = int(qax)
    qay = int(qay)
    msg = str(temp1)
    msg = msg.encode()
    r = 3
    rx,ry = point_mult(r,gx,gy)
    sx,sy =  point_mult(r,qax,qay)
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
    enc_msg = f1.encrypt(msg)
    enc_msg.decode()
    #requests.post("http://localhost:5001/t1", data={'msg': enc_msg, 'rx': rx, 'ry': ry})
    return enc_msg


@app.route("/ecc",methods=['POST'])
def hello():
    qax = request.form['qax']
    qay = request.form['qay']
    qax = int(qax)
    qay = int(qay)
    ard.write('a'.encode())
    time.sleep(5)
    msg = ard.read(ard.inWaiting()) # read all characters in buffer
    msg = msg.decode()
    print(msg)
    msg = (msg+":97:120.80:25")
    msg = msg.encode()
    r = 3
    rx,ry = point_mult(r,gx,gy)
    sx,sy =  point_mult(r,qax,qay)
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
    enc_msg = f1.encrypt(msg)
    enc_msg.decode()
    #requests.post("http://localhost:5001/t1", data={'msg': enc_msg, 'rx': rx, 'ry': ry})
    return enc_msg
if __name__ == "__main__":
    app.run(host="localhost",port=5001)
