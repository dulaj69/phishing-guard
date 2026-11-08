"""Local individual accounts and opaque, revocable browser sessions.

No email verification/recovery service is configured. Deploy behind HTTPS with
VTW_SECURE_COOKIE=1; this local prototype is not a completed identity platform.
"""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from warn import reliance

router = APIRouter(prefix='/account', tags=['Individual accounts'])
COOKIE = 'vtw_session'
TTL = 60 * 60 * 12


def connect():
    con = reliance._connect()
    con.row_factory = sqlite3.Row
    con.executescript('''
      CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
        salt TEXT NOT NULL, password_hash TEXT NOT NULL, created REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS account_sessions (token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL, expires REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS account_throttle (key TEXT PRIMARY KEY, attempts INTEGER NOT NULL, resets REAL NOT NULL);
      CREATE TABLE IF NOT EXISTS pilot_owners (token TEXT PRIMARY KEY, user_id TEXT NOT NULL);
    ''')
    return con


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def password_hash(password, salt):
    # PBKDF2-HMAC-SHA256, 600,000 iterations, independent 16-byte random salt.
    # The bundled macOS Python lacks hashlib.scrypt; never silently downgrade.
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000, dklen=32).hex()


def csrf(request: Request):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('x-research-request') != '1':
            raise HTTPException(403, 'Missing same-origin request marker.')
        origin = request.headers.get('origin')
        if origin and origin != f'{request.url.scheme}://{request.url.netloc}':
            raise HTTPException(403, 'Cross-origin account requests are not allowed.')
        if request.headers.get('sec-fetch-site') == 'cross-site':
            raise HTTPException(403, 'Cross-site account requests are not allowed.')


def current(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, 'Sign in to use your private research workspace.')
    with connect() as con:
        row = con.execute('SELECT a.id,a.username FROM accounts a JOIN account_sessions s ON s.user_id=a.id WHERE s.token_hash=? AND s.expires>?',
                          (digest(token), time.time())).fetchone()
    if not row:
        raise HTTPException(401, 'Your session expired. Please sign in again.')
    csrf(request)
    return dict(row)


def throttle(request, username):
    now = time.time()
    # Stored in SQLite so the limit survives server restarts and multiple workers.
    keys = [('ip:' + (request.client.host if request.client else 'unknown'), 30), ('name:' + username, 10)]
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        con.execute('DELETE FROM account_throttle WHERE resets<?', (now,))
        for key, maximum in keys:
            row = con.execute('SELECT * FROM account_throttle WHERE key=?', (digest(key),)).fetchone()
            if row and row['attempts'] >= maximum:
                raise HTTPException(429, 'Too many sign-in attempts. Please try again in 15 minutes.')
        for key, _ in keys:
            con.execute('INSERT INTO account_throttle VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET attempts=attempts+1', (digest(key), now+900))


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r'^[a-zA-Z0-9_\-]+$')
    password: str = Field(min_length=15, max_length=128)


def session(response, user):
    token = secrets.token_urlsafe(32)
    with connect() as con:
        con.execute('DELETE FROM account_sessions WHERE expires<?', (time.time(),))
        con.execute('INSERT INTO account_sessions VALUES (?,?,?)', (digest(token),user['id'],time.time()+TTL))
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite='strict',
                        secure=os.environ.get('VTW_SECURE_COOKIE')=='1', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return user


@router.post('/signup', status_code=201)
def signup(req: Credentials, request: Request, response: Response):
    csrf(request)
    name = req.username.lower()
    throttle(request, name)
    salt = secrets.token_hex(16)
    hashed = password_hash(req.password,salt)
    user = {'id':secrets.token_hex(16),'username':name}
    try:
        with connect() as con:
            con.execute('INSERT INTO accounts VALUES (?,?,?,?,?)', (user['id'],name,salt,hashed,time.time()))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'That username is unavailable.')
    return session(response,user)


@router.post('/login')
def login(req: Credentials, request: Request, response: Response):
    csrf(request)
    name = req.username.lower()
    throttle(request,name)
    with connect() as con:
        row = con.execute('SELECT * FROM accounts WHERE username=?', (name,)).fetchone()
    actual = password_hash(req.password, row['salt'] if row else '00'*16)
    if not row or not hmac.compare_digest(actual,row['password_hash']):
        raise HTTPException(401,'Username or password is incorrect.')
    return session(response,{'id':row['id'],'username':row['username']})


@router.get('/me')
def me(user=Depends(current)):
    return user


@router.post('/logout')
def logout(request:Request, response:Response, user=Depends(current)):
    with connect() as con:
        con.execute('DELETE FROM account_sessions WHERE token_hash=?',(digest(request.cookies[COOKIE]),))
    response.delete_cookie(COOKIE,path='/')
    return {'signed_out':True}


def own_pilot(token, user):
    with connect() as con:
        row = con.execute('SELECT user_id FROM pilot_owners WHERE token=?',(token,)).fetchone()
    if not row or row['user_id'] != user['id']:
        raise HTTPException(404,'Study session not found in your account.')
