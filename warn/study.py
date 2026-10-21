"""Server-owned, single-use trial records; no SMS text or client-provided truth."""
import secrets
import time
from warn import reliance


def connect():
    con = reliance._connect()
    con.execute('''CREATE TABLE IF NOT EXISTS trials (
      token TEXT PRIMARY KEY, user_id TEXT, message_id TEXT, initial_choice TEXT,
      ai_advice TEXT, truth TEXT, condition TEXT, session INTEGER, intervention TEXT,
      created REAL, consumed INTEGER DEFAULT 0)''')
    return con


def create(user, scenario, initial, result, condition, session):
    token = secrets.token_urlsafe(24)
    with connect() as con:
        con.execute('INSERT INTO trials VALUES (?,?,?,?,?,?,?,?,?,?,0)',
                    (token, user, scenario['id'], initial, result['ai_advice'], scenario['truth'],
                     condition, session, result['warning']['intervention'], time.time()))
    return token


def record(token, user, final, action, seconds):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT user_id,message_id,initial_choice,ai_advice,truth,condition,session,intervention,created,consumed FROM trials WHERE token=?', (token,)).fetchone()
        if not row or row[0] != user or row[-1] or time.time() - row[-2] > 7200:
            raise ValueError('Unknown, expired, or already completed study trial.')
        # Insert and consume atomically, including uncertain advice (excluded from RAIR/RSR).
        con.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    (user, row[1], row[6], row[5], row[2], row[3], final, row[4], action,
                     row[7], seconds, time.time()))
        con.execute('UPDATE trials SET consumed=1 WHERE token=?', (token,))
    return reliance.profile(user, condition=row[5], session=row[6])
