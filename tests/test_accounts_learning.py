from fastapi.testclient import TestClient
from api.main import app
from api import accounts
from research.lab import learning
import time

PASSWORD='a long fictional test passphrase'

def member(name):
    c=TestClient(app,headers={'X-Research-Request':'1'})
    r=c.post('/account/signup',json={'username':name,'password':PASSWORD})
    assert r.status_code==201, r.text
    return c,r.json()

def test_auth_required_public_checker_still_open():
    c=TestClient(app)
    assert c.get('/account/me').status_code==401
    assert c.get('/research/catalog').status_code==401
    assert c.get('/learning/sessions').status_code==401
    assert c.get('/profile/someone').status_code==401
    assert c.get('/app/lab/',follow_redirects=False).status_code==307
    assert c.post('/analyze',json={'text':'Never share your OTP.'}).status_code==200
    assert c.post('/analyze',json={'text':'x','study_mode':True}).status_code==401

def test_password_storage_logout_expiry_and_login():
    c,u=member('member_one')
    token=c.cookies.get(accounts.COOKIE)
    with accounts.connect() as con:
        row=con.execute('SELECT * FROM accounts').fetchone()
        assert row['password_hash']!=PASSWORD and len(row['salt'])==32
        assert con.execute('SELECT token_hash FROM account_sessions').fetchone()[0]!=token
    assert c.get('/account/me').json()==u
    assert c.post('/account/logout',json={}).status_code==200
    c.cookies.set(accounts.COOKIE,token)
    assert c.get('/account/me').status_code==401
    c.cookies.clear()
    assert c.post('/account/login',json={'username':'MEMBER_ONE','password':PASSWORD}).status_code==200
    with accounts.connect() as con:con.execute('UPDATE account_sessions SET expires=?',(time.time()-1,))
    assert c.get('/account/me').status_code==401

def test_cross_origin_missing_marker_and_account_limits():
    c=TestClient(app)
    payload={'username':'member_one','password':PASSWORD}
    assert c.post('/account/signup',json=payload).status_code==403
    c.headers['X-Research-Request']='1'
    assert c.post('/account/signup',json=payload,headers={'Origin':'https://attacker.example'}).status_code==403
    assert c.post('/account/signup',json={**payload,'password':'short'}).status_code==422
    assert c.post('/account/signup',json=payload).status_code==201
    assert c.post('/account/signup',json=payload).status_code==409
    for _ in range(8):
        assert c.post('/account/login',json={**payload,'password':'an incorrect passphrase'}).status_code==401
    assert c.post('/account/login',json=payload).status_code==429

def test_owner_isolation_for_learning_and_existing_pilot():
    a,_=member('alice');b,_=member('bob')
    s=a.post('/learning/sessions',json={'consent':True}).json();token=s['id']
    assert b.get('/learning/sessions').json()['sessions']==[]
    for suffix in ('','/report'):
        assert b.get('/learning/sessions/'+token+suffix).status_code==404
    assert b.post('/learning/sessions/'+token+'/answer',json={'index':0,'choice':'safe','reason':0,'confidence':50}).status_code==404
    p=a.post('/research/pilot/sessions',json={'mode':'rehearsal'}).json()['session_id']
    assert a.get('/research/pilot/'+p).status_code==200
    assert b.get('/research/pilot/'+p).status_code==404
    assert b.get('/research/pilot/'+p+'/report').status_code==404

def test_learning_sequence_targeting_transfer_and_delayed_gate(monkeypatch):
    c,u=member('learner')
    assert c.post('/learning/sessions',json={}).status_code==422
    s=c.post('/learning/sessions',json={'consent':True}).json();token=s['id'];base='/learning/sessions/'+token
    with learning.connect() as con:con.execute("UPDATE learning_sessions SET condition='adaptive' WHERE id=?",(token,))
    assert c.post('/learning/sessions',json={'consent':True}).json()['id']==token
    assert c.post(base+'/lesson',json={}).status_code==409
    for i in range(3):
        assert 'truth' not in s['item'] and 'answer' not in s['item']
        item=learning.ITEMS[i]
        # Only borrowed identity is wrong, confidently: it must win adaptation.
        data={'index':i,'choice':'safe' if i==1 else item['truth'],'reason':learning.option_order(token,i).index(0 if i==1 else item['answer']),'confidence':100}
        result=c.post(base+'/answer',json=data);assert result.status_code==200
        s=result.json()
        assert c.post(base+'/answer',json=data).status_code==409
    assert s['stage']=='lesson' and s['lesson']['title']=='Verify the requested route'
    assert c.get(base+'/report').json()['lesson_selection'][0]['concept']=='borrowed_identity'
    assert c.post(base+'/answer',json={'index':3,'choice':'safe','reason':0,'confidence':50}).status_code==409
    s=c.post(base+'/lesson',json={}).json()
    assert s['stage']=='transfer' and s['lesson'] is None
    for i in range(3,6):
        item=learning.ITEMS[i]
        s=c.post(base+'/answer',json={'index':i,'choice':item['truth'],'reason':learning.option_order(token,i).index(item['answer']),'confidence':100}).json()
    assert s['stage']=='waiting'
    r=c.get(base+'/report').json()
    assert r['phases']['transfer']['correct']==3 and r['phases']['transfer']['confidence_error']==0
    assert r['phases']['delayed']['accuracy'] is None
    assert c.post(base+'/answer',json={'index':6,'choice':'scam','reason':0,'confidence':50}).status_code==409
    session_cookie=c.cookies.get(accounts.COOKIE)
    future=time.time()+learning.DELAY_SECONDS+1
    # Test clock seam; no public skip-waiting parameter exists.
    monkeypatch.setattr(learning.time,'time',lambda:future)
    # Extend account session too: normal users sign back in after 12 hours.
    with accounts.connect() as con:con.execute('UPDATE account_sessions SET expires=?',(future+3600,))
    c.cookies.clear()
    c.cookies.set(accounts.COOKIE,session_cookie)
    assert c.get(base).json()['stage']=='delayed'
    for i in range(6,9):
        item=learning.ITEMS[i]
        s=c.post(base+'/answer',json={'index':i,'choice':item['truth'],'reason':learning.option_order(token,i).index(item['answer']),'confidence':100}).json()
    assert s['stage']=='complete'
    assert c.get(base+'/report').json()['phases']['delayed']['correct']==3

def test_partial_reports_do_not_reveal_answer_keys_and_static_is_fixed():
    c,_=member('static_learner')
    token=c.post('/learning/sessions',json={'consent':True}).json()['id'];base='/learning/sessions/'+token
    with learning.connect() as con:con.execute("UPDATE learning_sessions SET condition='static' WHERE id=?",(token,))
    for i in range(3):
        s=c.post(base+'/answer',json={'index':i,'choice':'safe','reason':1,'confidence':90}).json()
        if i<2:
            r=c.get(base+'/report').json()
            assert r['phases']['baseline']['correct'] is None and not r['lesson_selection']
    assert s['lesson']['title']=='Protect the secret'

def test_legacy_study_identity_is_bound_to_account_and_cookies_are_protected(monkeypatch):
    monkeypatch.setenv('VTW_SECURE_COOKIE','1')
    secure=TestClient(app,base_url='https://testserver',headers={'X-Research-Request':'1'})
    r=secure.post('/account/signup',json={'username':'secure_member','password':PASSWORD})
    cookie=r.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie and 'secure' in cookie
    assert secure.get('/account/me').headers['cache-control']=='no-store'
    monkeypatch.delenv('VTW_SECURE_COOKIE')
    a,owner=member('study_owner');b,_=member('study_other')
    scenario=a.get('/scenarios').json()[0]
    analyzed=a.post('/analyze',json={'text':scenario['text'],'sender':scenario['sender'],
        'study_mode':True,'user_id':'arbitrary','scenario_id':scenario['id'],'initial_choice':'safe'}).json()
    decision={'user_id':'account:'+owner['id'],'message_id':scenario['id'],'analysis_id':analyzed['analysis_id'],'ai_advice':'scam','final_choice':'scam'}
    assert b.post('/decision',json=decision).status_code==409
    assert a.post('/decision',json=decision).status_code==200
    assert b.get('/profile/account:'+owner['id']).json()['decisions']==0
    assert a.get('/profile/arbitrary').json()['decisions']==1
