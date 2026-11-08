"""Server-assigned pilot with six advice trials and three no-advice transfer trials.
Rehearsals are explicitly separated from consented pilot sessions. No SMS text is stored.
"""
import json
import secrets
import time
from api.pipeline import analyze
from warn import reliance

# Distinct authored items; not a validated psychometric instrument.
ITEMS = [
    {'id': 'p1', 'text': 'Demo Bank: reply with your OTP to stop this transfer.', 'truth': 'scam', 'phase': 'advice', 'planted': False},
    {'id': 'p2', 'text': 'Orion Bank: Your account was credited with LKR 800. No action is required.', 'truth': 'safe', 'phase': 'advice', 'planted': False},
    {'id': 'p3', 'text': 'Orion Bank: account blocked. Call 0771234567 immediately.', 'truth': 'scam', 'phase': 'advice', 'planted': True},
    {'id': 'p4', 'text': 'Demo Bank: Your OTP is 123456. Never share your OTP.', 'truth': 'safe', 'phase': 'advice', 'planted': True},
    {'id': 'p5', 'text': 'Demo Bank: send your PIN to restore access.', 'truth': 'scam', 'phase': 'advice', 'planted': False},
    {'id': 'p6', 'text': 'Orion Bank: Your monthly statement is available in your usual banking app.', 'truth': 'safe', 'phase': 'advice', 'planted': False},
    {'id': 't1', 'text': 'Demo Bank: provide the verification code to cancel the suspicious payment.', 'truth': 'scam', 'phase': 'transfer', 'planted': False},
    {'id': 't2', 'text': 'Orion Bank: Rs 950 debited from your account. Check your usual bank app for details.', 'truth': 'safe', 'phase': 'transfer', 'planted': False},
    {'id': 't3', 'text': 'Demo Bank: your card will be blocked today. Call 0762223344 to keep it active.', 'truth': 'scam', 'phase': 'transfer', 'planted': False},
]
QUESTIONS = [
    {'id': 'q1', 'text': 'Does a matching bank name prove who sent the SMS?',
     'options': ['Yes', 'No', 'Only if it is urgent'], 'answer': 1},
    {'id': 'q2', 'text': 'Where should you get a contact number to verify an unexpected request?',
     'options': ['Your bank card or independently opened bank app', 'Only the incoming SMS', 'Any number with the bank name'], 'answer': 0},
    {'id': 'q3', 'text': 'If a number is missing from an incomplete registry, what does that establish?',
     'options': ['Definitely fraudulent', 'Definitely genuine', 'Not verified by that registry'], 'answer': 2},
]
CONDITIONS = ('static', 'user_only', 'evidence_aware')


def connect():
    con = reliance._connect()
    con.row_factory = __import__('sqlite3').Row
    con.execute('''CREATE TABLE IF NOT EXISTS lab_sessions (
        id TEXT PRIMARY KEY, mode TEXT, condition TEXT, ordering TEXT, next_index INTEGER,
        created REAL, completed REAL)''')
    con.execute('''CREATE TABLE IF NOT EXISTS lab_trials (
        session_id TEXT, idx INTEGER, item_id TEXT, initial TEXT, initial_confidence INTEGER,
        advice TEXT, intervention TEXT, final TEXT, final_confidence INTEGER, action TEXT,
        comprehension INTEGER, started REAL, completed REAL, warning TEXT,
        PRIMARY KEY(session_id, idx))''')
    return con


def create(mode, consent):
    if mode == 'pilot' and not consent:
        raise ValueError('Pilot logging requires explicit consent. Use rehearsal for a demonstration.')
    rng = secrets.SystemRandom()
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        counts = {c: con.execute('SELECT count(*) FROM lab_sessions WHERE mode=? AND condition=?', (mode,c)).fetchone()[0] for c in CONDITIONS}
        minimum = min(counts.values())
        condition = rng.choice([c for c in CONDITIONS if counts[c] == minimum])
        guided = [i for i in range(6)]; transfer = [i for i in range(6,9)]
        rng.shuffle(guided); rng.shuffle(transfer)
        token = secrets.token_urlsafe(24)
        con.execute('INSERT INTO lab_sessions VALUES (?,?,?,?,0,?,NULL)',
                    (token, mode, condition, json.dumps(guided+transfer), time.time()))
    return status(token)


def session(con, token):
    s = con.execute('SELECT * FROM lab_sessions WHERE id=?', (token,)).fetchone()
    if not s:
        raise ValueError('Unknown pilot session')
    return dict(s)


def status(token):
    with connect() as con:
        s = session(con, token)
    item = ITEMS[json.loads(s['ordering'])[s['next_index']]] if s['next_index'] < 9 else None
    return {'session_id': token, 'mode': s['mode'], 'condition': s['condition'], 'completed': s['next_index'], 'total': 9,
            'item': {k: item[k] for k in ('id','text','phase')} if item else None,
            'debrief': ('Two advice trials intentionally supplied incorrect AI advice. All bank details were fictional. '
                        'The final three trials had no AI advice. This short pilot does not demonstrate long-term learning.') if not item else None}


def begin(token, index, choice, confidence):
    with connect() as con:
        s = session(con, token)
        if s['next_index'] != index or index >= 9:
            raise ValueError('This is not the active trial')
        existing = con.execute('SELECT * FROM lab_trials WHERE session_id=? AND idx=?', (token,index)).fetchone()
        if existing:
            if existing['initial'] != choice or existing['initial_confidence'] != confidence:
                raise ValueError('Initial response is already locked')
            warning = json.loads(existing['warning'])
            advice = existing['advice']
        else:
            item = ITEMS[json.loads(s['ordering'])[index]]
            if item['phase'] == 'advice':
                r = analyze(item['text'], language='en', user_id='lab:'+token,
                            planted_error=item['planted'], study_truth=item['truth'],
                            condition=s['condition'], session=1)
                warning, advice = r['warning'], r['ai_advice']
            else:
                warning, advice = None, 'none'
            con.execute('INSERT INTO lab_trials VALUES (?,?,?,?,?,?,?,NULL,NULL,NULL,NULL,?,NULL,?)',
                        (token,index,item['id'],choice,confidence,advice,
                         warning['intervention'] if warning else 'no_advice',time.time(),json.dumps(warning)))
    q = QUESTIONS[index % len(QUESTIONS)]
    return {'index': index, 'warning': warning, 'ai_advice': advice,
            'question': {k:q[k] for k in ('id','text','options')} if index < 6 else None}


def finish(token, index, choice, confidence, action, comprehension):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        s = session(con, token)
        row = con.execute('SELECT * FROM lab_trials WHERE session_id=? AND idx=?', (token,index)).fetchone()
        if s['next_index'] != index or not row or row['completed'] is not None:
            raise ValueError('Trial is missing, out of order, or already completed')
        if index < 6 and comprehension is None:
            raise ValueError('Answer the evidence-comprehension question')
        item = next(i for i in ITEMS if i['id'] == row['item_id'])
        correct = int(comprehension == QUESTIONS[index % 3]['answer']) if index < 6 else None
        now = time.time()
        con.execute('UPDATE lab_trials SET final=?,final_confidence=?,action=?,comprehension=?,completed=? WHERE session_id=? AND idx=?',
                    (choice,confidence,action,correct,now,token,index))
        # Only labelled advice trials update reliance; transfer measures independent decisions.
        if item['phase'] == 'advice':
            con.execute('INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        ('lab:'+token,item['id'],1,s['condition'],row['initial'],row['advice'],choice,
                         item['truth'],action,row['intervention'],now-row['started'],now))
        con.execute('UPDATE lab_sessions SET next_index=?,completed=? WHERE id=?', (index+1,now if index == 8 else None,token))
    return {'next': status(token), 'feedback': ('Recorded. Feedback is withheld during transfer trials.' if index >= 6 else
            f'This fictional scenario was labelled {item["truth"]}. Use independently obtained bank details for verification.')}


def report(token):
    with connect() as con:
        s = session(con,token)
        rows = [dict(r) for r in con.execute('SELECT * FROM lab_trials WHERE session_id=? AND completed IS NOT NULL ORDER BY idx',(token,))]
    details = []
    for r in rows:
        item = next(i for i in ITEMS if i['id']==r['item_id'])
        details.append({'item_id':item['id'],'phase':item['phase'],'initial':r['initial'], 'final':r['final'],
            'truth':item['truth'],'advice':r['advice'],'correct':r['final']==item['truth'],
            'initial_confidence':r['initial_confidence'],'final_confidence':r['final_confidence'],
            'action':r['action'],'comprehension_correct':r['comprehension'],
            'post_initial_seconds':round(r['completed']-r['started'],2)})
    groups = {}
    for phase in ('advice','transfer'):
        group = [r for r in details if r['phase']==phase]
        groups[phase]={'n':len(group),'correct':sum(r['correct'] for r in group),
                       'accuracy':sum(r['correct'] for r in group)/len(group) if group else None}
    # Do not reveal transfer answers before the entire no-advice block finishes.
    if s['next_index'] < 9:
        groups['transfer']['correct'] = None
        groups['transfer']['accuracy'] = None
        for detail in details:
            if detail['phase'] == 'transfer':
                detail.pop('truth', None)
                detail.pop('correct', None)
    p = reliance.profile('lab:'+token, condition=s['condition'], session=1)
    return {'kind':'rehearsal' if s['mode']=='rehearsal' else 'pilot_observation',
            'condition':s['condition'],'completed':len(rows),'phases':groups,
            'reliance':{k:p[k] for k in ('RAIR','RSR','RAIR_opportunities','RSR_opportunities')},
            'rows':details,
            'limitation':'One short session on authored English fixtures; immediate transfer is not durable learning. No population or causal claim.'}
