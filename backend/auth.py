"""Password hashing and database-backed, revocable cookie sessions."""
import base64
import hashlib
import hmac
import os
import secrets
import time
from contextlib import closing
from threading import Lock
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
import re

router = APIRouter(prefix='/api/auth')
ITERATIONS = 600_000
COOKIE = 'campus_session'
TTL = 60 * 60 * 24
SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
PUBLIC_FIELDS = 'id, name, first_name, last_name, email, created_at'
connect = None  # configured by main.py
_attempts = {}
_lock = Lock()


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt}${base64.b64encode(digest).decode()}'


def verify_password(password, encoded):
    try:
        parts = encoded.split('$')
        if len(parts) == 3 and parts[0] == 'pbkdf2_sha256':
            _, salt, expected = parts
            actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120_000).hex()
        else:
            algorithm, iterations, salt, expected = parts
            if algorithm != 'pbkdf2_sha256' or not 1 <= int(iterations) <= 2_000_000:
                return False
            actual = base64.b64encode(hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations))).decode()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


def initialize():
    with closing(connect()) as db, db:
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS users_email_ci ON users(lower(email))')
        db.execute('''CREATE TABLE IF NOT EXISTS auth_sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            expires_at INTEGER NOT NULL)''')


def guard(request):
    # A non-simple header plus JSON prevents cross-origin form submissions;
    # no cross-origin origins are allowed by CORS.
    if request.headers.get('x-campus-request') != '1' or request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Request not allowed')
    key = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    with _lock:
        for old in list(_attempts):
            _attempts[old] = [t for t in _attempts[old] if now-t < 60]
            if not _attempts[old]: del _attempts[old]
        recent = _attempts.setdefault(key, [])
        if len(recent) >= 15:
            raise HTTPException(429, 'Too many attempts. Please wait a minute.', headers={'Retry-After': '60'})
        recent.append(now)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session(db, user_id, request, response):
    old = request.cookies.get(COOKIE)
    if old: db.execute('DELETE FROM auth_sessions WHERE token_hash=?', (token_hash(old),))
    token = secrets.token_urlsafe(32)
    db.execute('DELETE FROM auth_sessions WHERE expires_at <= ?', (int(time.time()),))
    db.execute('INSERT INTO auth_sessions VALUES (?, ?, ?)', (token_hash(token), user_id, int(time.time())+TTL))
    response.delete_cookie(COOKIE, path='/api/auth')
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, secure=SECURE, samesite='strict', path='/api')
    response.headers['Cache-Control'] = 'no-store'
    return dict(db.execute(f'SELECT {PUBLIC_FIELDS} FROM users WHERE id=?', (user_id,)).fetchone())


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    confirm_password: str = Field(min_length=1, max_length=128)


def email_address(value):
    email = value.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Please enter a valid email address.')
    return email


@router.post('/register', status_code=201)
def register(body: Register, request: Request, response: Response):
    guard(request)
    email = email_address(body.email)
    first, last = body.first_name.strip(), body.last_name.strip()
    if not first or not last: raise HTTPException(422, 'First and last name are required.')
    if len(body.password) < 12: raise HTTPException(422, 'Use a password with at least 12 characters.')
    if body.password != body.confirm_password: raise HTTPException(422, 'Passwords do not match.')
    hashed = hash_password(body.password)
    import sqlite3
    with closing(connect()) as db, db:
        try:
            row = db.execute('INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)',
                             (f'{first} {last}', first, last, email, hashed))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'An account with this email already exists. Please log in.')
        return session(db, row.lastrowid, request, response)


@router.post('/login')
def login(body: Login, request: Request, response: Response):
    guard(request)
    email = email_address(body.email)
    with closing(connect()) as db, db:
        user = db.execute('SELECT * FROM users WHERE lower(email)=?', (email,)).fetchone()
        valid = verify_password(body.password, user['password_hash'] if user else DUMMY_HASH)
        if not user or not valid: raise HTTPException(401, 'Incorrect email or password.')
        if len(user['password_hash'].split('$')) == 3:
            db.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(body.password), user['id']))
        return session(db, user['id'], request, response)


@router.get('/me')
def me(request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    with closing(connect()) as db:
        row = db.execute(f'SELECT {", ".join("u."+f.strip() for f in PUBLIC_FIELDS.split(","))} FROM users u JOIN auth_sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?',
                         (token_hash(request.cookies.get(COOKIE, '')), int(time.time()))).fetchone()
        if not row: raise HTTPException(401, 'Please log in.')
        return dict(row)


@router.post('/logout', status_code=204)
def logout(request: Request, response: Response):
    guard(request)
    with closing(connect()) as db, db:
        db.execute('DELETE FROM auth_sessions WHERE token_hash=?', (token_hash(request.cookies.get(COOKIE, '')),))
    response.delete_cookie(COOKIE, path='/api/auth')
    response.delete_cookie(COOKIE, path='/api', httponly=True, secure=SECURE, samesite='strict')
    response.headers['Cache-Control'] = 'no-store'


def current_user(request):
    token = request.cookies.get(COOKIE)
    if not token: return None
    with closing(connect()) as db:
        row = db.execute('SELECT u.id, u.name, u.email FROM users u JOIN auth_sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?', (token_hash(token), int(time.time()))).fetchone()
    if row is None: raise HTTPException(401, 'Your session expired. Please log in again.')
    return dict(row)
