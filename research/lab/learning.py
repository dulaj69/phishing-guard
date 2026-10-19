"""Misconception-targeted teaching with separate, server-gated transfer blocks.
Authored English instruments, not a validated psychological or security scale.
"""
import secrets
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from api import accounts

router = APIRouter(prefix='/learning', tags=['Personal learning lab'], dependencies=[Depends(accounts.current)])
DELAY_SECONDS = 24*60*60
CONCEPTS = {
 'credentials': {'title':'Protect the secret', 'weight':3, 'lesson':'A request to disclose an OTP, PIN or password is the important action. A polite tone or familiar sender name does not make that request safe. A message that says never share an OTP is different: it prohibits the harmful action.', 'step':'Keep secrets private. If concerned, open your bank app yourself.'},
 'borrowed_identity': {'title':'Verify the requested route', 'weight':2, 'lesson':'An official-looking domain or familiar bank name can be copied into any message. Check the route you are asked to use, such as a callback number, against a separately obtained official source. A matching detail does not authenticate the entire message.', 'step':'Use the number on your bank card, not a number supplied by the message.'},
 'uncertainty': {'title':'Unknown is not safe', 'weight':2, 'lesson':'Missing evidence does not prove fraud or legitimacy. A low model score is also not proof. When a claim cannot be verified, choose an independent check instead of turning uncertainty into confidence.', 'step':'Pause, keep the message and confirm the request independently.'}
}
# Different texts for baseline, immediate transfer and delayed transfer. Native-language
# adaptation and expert difficulty matching are prerequisites for a real study.
ITEMS = [
 ('b1','baseline','credentials','Cedar Bank support: please reply with your OTP to finish our security check.','scam',['It requests a secret code.','It sounds polite.','It has no link.'],0),
 ('b2','baseline','borrowed_identity','Cedar Bank notice: our website is cedar.example. Call 077 123 4567 now to prevent a freeze. The supplied number has not been independently verified.','scam',['The website name proves the caller is genuine.','The requested callback route is unverified.','All telephone calls are fraudulent.'],1),
 ('b3','baseline','uncertainty','Security reminder: if a payment looks unfamiliar, open the banking app you already use yourself and check it there. No reply or link is requested.','safe',['The sender is certainly genuine.','A model would give this a low score.','It directs you to an independently opened app without requesting secrets.'],2),
 ('t1','transfer','credentials','Keep your one-time passcode private. Our staff will never ask you to send it in a message.','safe',['It prohibits sharing the secret.','Every message mentioning OTP is a scam.','The word staff proves authenticity.'],0),
 ('t2','transfer','borrowed_identity','Concerned about an account notification? Use the number already printed on your bank card. Do not call a number in an unexpected message.','safe',['Any phone number is safe.','It asks you to use a separately obtained contact route.','The writing style proves the sender.'],1),
 ('t3','transfer','uncertainty','A transfer is waiting. The checker found no matching bank evidence and gives a low score. Send your account password here to release it.','scam',['No matching evidence means safe.','Low score proves the sender.','A low score does not override the password request.'],2),
 ('d1','delayed','credentials','To cancel a disputed transaction, read your login code to our agent on this chat.','scam',['The request would reveal a secret.','Cancelling a transaction is always safe.','Chat support can always ask for codes.'],0),
 ('d2','delayed','borrowed_identity','A message displays a genuine bank logo but asks you to install a support app from a new link. The app has not been verified.','scam',['A genuine logo authenticates the app.','A copied identity does not verify the requested installation.','Every app is malicious.'],1),
 ('d3','delayed','uncertainty','You cannot verify an unexpected account claim. You choose to ignore its link and ask your bank through the app you independently opened.','safe',['You have proved the message is legitimate.','You have proved it is fraud.','You can choose a safer action while the claim remains unknown.'],2),
]
ITEMS = [dict(id=i,phase=p,concept=c,text=t,truth=y,reasons=r,answer=a) for i,p,c,t,y,r,a in ITEMS]


def connect():
    con = accounts.connect()
    con.executescript('''
      CREATE TABLE IF NOT EXISTS learning_sessions (id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
        condition TEXT NOT NULL, next_index INTEGER NOT NULL DEFAULT 0, lesson TEXT,
        lesson_read INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, due REAL,
        completed REAL, consent_version TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS learning_answers (session_id TEXT NOT NULL, idx INTEGER NOT NULL,
        choice TEXT NOT NULL, reason INTEGER NOT NULL, confidence INTEGER NOT NULL,
        created REAL NOT NULL, PRIMARY KEY(session_id,idx));
    ''')
    return con


def get(con, token, user):
    row = con.execute('SELECT * FROM learning_sessions WHERE id=? AND user_id=?',(token,user['id'])).fetchone()
    if not row: raise HTTPException(404,'Learning session not found in your account.')
    return dict(row)


def option_order(token, idx):
    # Stable within a session, varied between sessions; never make answer position
    # a reliable shortcut for a concept. Store canonical reason indices in SQLite.
    return sorted(range(3), key=lambda i: accounts.digest(f'{token}:{idx}:{i}'))


def status(row):
    idx=row['next_index']; stage='complete'; item=None
    if idx < 3: stage='baseline'
    elif not row['lesson_read']: stage='lesson'
    elif idx < 6: stage='transfer'
    elif idx < 9: stage='delayed' if time.time() >= row['due'] else 'waiting'
    if stage in ('baseline','transfer','delayed'):
        item={k:v for k,v in ITEMS[idx].items() if k not in ('truth','answer')}
        item['reasons']=[ITEMS[idx]['reasons'][i] for i in option_order(row['id'],idx)]
    return {'id':row['id'],'condition':row['condition'],'stage':stage,'index':idx,
            'item':item,'due':row['due'],'lesson':CONCEPTS[row['lesson']] if row['lesson'] and stage in ('lesson','waiting','complete') else None,
            'instrument_version':'misconceptions-en-v1','completed':idx}


class Start(BaseModel):
    consent:bool=False


@router.post('/sessions')
def start(req:Start,user=Depends(accounts.current)):
    if not req.consent: raise HTTPException(422,'Confirm the learning-session data notice before starting.')
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        existing=con.execute('SELECT * FROM learning_sessions WHERE user_id=? AND next_index<9 ORDER BY created DESC LIMIT 1',(user['id'],)).fetchone()
        if existing:return status(dict(existing))
        token=secrets.token_urlsafe(24)
        con.execute('INSERT INTO learning_sessions(id,user_id,condition,created,consent_version) VALUES (?,?,?,?,?)',
                    (token,user['id'],secrets.choice(['adaptive','static']),time.time(),'local-learning-v1'))
        return status(get(con,token,user))


@router.get('/sessions')
def history(user=Depends(accounts.current)):
    with connect() as con:
        rows=con.execute('SELECT * FROM learning_sessions WHERE user_id=? ORDER BY created DESC',(user['id'],)).fetchall()
    return {'sessions':[dict(id=r['id'],created=r['created'],condition=r['condition'],completed=r['next_index'],due=r['due']) for r in rows],
            'notice':'Private individual practice records. Authored English questions; repeated attempts are not independent participants.'}


@router.get('/sessions/{token}')
def resume(token:str,user=Depends(accounts.current)):
    with connect() as con:return status(get(con,token,user))


class Answer(BaseModel):
    index:int=Field(ge=0,le=8)
    choice:Literal['safe','scam']
    reason:int=Field(ge=0,le=2)
    confidence:int=Field(ge=0,le=100)


def priorities(rows):
    ranking=[]
    for r in rows:
        item=ITEMS[r['idx']]
        wrong=int(r['choice']!=item['truth']); misconception=int(r['reason']!=item['answer'])
        value=CONCEPTS[item['concept']]['weight']*(wrong+misconception)*(1+r['confidence']/100)
        ranking.append({'concept':item['concept'],'priority':round(value,3),'judgement_incorrect':bool(wrong),
                        'reason_incorrect':bool(misconception),'confidence':r['confidence']})
    return sorted(ranking,key=lambda r:(-r['priority'],r['concept']))


@router.post('/sessions/{token}/answer')
def answer(token:str,req:Answer,user=Depends(accounts.current)):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row=get(con,token,user)
        if status(row)['stage'] not in ('baseline','transfer','delayed') or req.index!=row['next_index']:
            raise HTTPException(409,'This answer is not for the current open trial. Reload your session.')
        con.execute('INSERT INTO learning_answers VALUES (?,?,?,?,?,?)',(token,req.index,req.choice,option_order(token,req.index)[req.reason],req.confidence,time.time()))
        idx=req.index+1
        con.execute('UPDATE learning_sessions SET next_index=? WHERE id=?',(idx,token))
        if idx==3:
            rows=con.execute('SELECT * FROM learning_answers WHERE session_id=? ORDER BY idx',(token,)).fetchall()
            lesson=priorities(rows)[0]['concept'] if row['condition']=='adaptive' else 'credentials'
            con.execute('UPDATE learning_sessions SET lesson=? WHERE id=?',(lesson,token))
        if idx==6: con.execute('UPDATE learning_sessions SET due=? WHERE id=?',(time.time()+DELAY_SECONDS,token))
        if idx==9: con.execute('UPDATE learning_sessions SET completed=? WHERE id=?',(time.time(),token))
        return status(get(con,token,user))


@router.post('/sessions/{token}/lesson')
def lesson_read(token:str,user=Depends(accounts.current)):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row=get(con,token,user)
        if status(row)['stage']!='lesson':raise HTTPException(409,'Complete baseline questions before the lesson.')
        con.execute('UPDATE learning_sessions SET lesson_read=1 WHERE id=?',(token,))
        return status(get(con,token,user))


@router.get('/sessions/{token}/report')
def report(token:str,user=Depends(accounts.current)):
    with connect() as con:
        row=get(con,token,user)
        answers=con.execute('SELECT * FROM learning_answers WHERE session_id=? ORDER BY idx',(token,)).fetchall()
    phases={}
    for phase in ('baseline','transfer','delayed'):
        subset=[r for r in answers if ITEMS[r['idx']]['phase']==phase]
        complete=len(subset)==3
        correct=sum(r['choice']==ITEMS[r['idx']]['truth'] for r in subset)
        phases[phase]={'n':len(subset),'correct':correct if complete else None,'accuracy':correct/3 if complete else None,
          'reason_correct':sum(r['reason']==ITEMS[r['idx']]['answer'] for r in subset) if complete else None,
          'confidence_error':round(sum((r['confidence']/100-int(r['choice']==ITEMS[r['idx']]['truth']))**2 for r in subset)/3,4) if complete else None}
    baseline=[r for r in answers if r['idx']<3]
    return {'session':status(row),'phases':phases,
      'lesson_selection':priorities(baseline) if len(baseline)==3 else [],
      'priority_formula':'harm weight × (incorrect judgement + incorrect reason) × (1 + confidence / 100)',
      'gain':phases['transfer']['accuracy']-phases['baseline']['accuracy'] if phases['transfer']['accuracy'] is not None else None,
      'limitation':'Only three authored English questions per block. Immediate change is descriptive, not proof that teaching caused learning. Static and adaptive lessons require a sufficiently powered, approved between-person study. Delayed transfer unlocks 24 hours after immediate transfer; no delayed result is inferred.'}
