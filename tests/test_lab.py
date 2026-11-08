import pytest
from fastapi.testclient import TestClient
from api.main import app
from research.lab import evidence, pilot
from research.lab.cases import CASES
from warn import reliance

client=TestClient(app)


@pytest.fixture(autouse=True)
def signed_in(temp_reliance_db):
    client.cookies.clear()
    client.headers.update({'X-Research-Request':'1'})
    result=client.post('/account/signup',json={'username':'test_researcher','password':'a long test passphrase'})
    assert result.status_code==201


def test_workbench_and_catalog():
    assert client.get('/', follow_redirects=False).headers['location'] == '/app/'
    assert 'Research workbench' in client.get('/app/lab/').text
    assert 'study' not in client.get('/app/').text.split('<nav')[1].split('</nav>')[0]
    assert 'Under the hood' in client.get('/app/study/').text
    c=client.get('/research/catalog').json()
    assert len(c['contributions'])==3 and len(c['cases'])==18
    assert c['model_fingerprint']


def test_robustness_and_benchmark_keep_errors_visible():
    r=client.post('/research/robustness',json={'case_id':'otp-en'}).json()
    assert r['rows'][0]['operator']=='original' and len(r['rows'])>=4
    assert r['summary']['correct_actions']<=r['summary']['variants']
    b=client.post('/research/benchmark',json={}).json()
    assert b['cases']==len(CASES) and len(b['rows'])==len(CASES)
    assert sum(g['n'] for g in b['per_language'])==len(CASES)
    assert 'possible training overlap' in b['limitation']
    assert client.post('/research/robustness',json={'case_id':'invalid'}).status_code==409


def test_evidence_audit_finds_decisive_contradiction():
    r=evidence.run('callback',.55,True,True,False,False,False)
    assert r['risk']['tier']=='High'
    decisive=next(x for x in r['removal_audit'] if x['removed']=='contradiction')
    assert decisive['decision_changed']
    assert r['minimal_sufficient_sets']==[['contradiction']]
    assert evidence.run('callback',.55,True,True,True,False,False)['risk']['abstain']
    assert evidence.run('callback',.55,True,True,False,True,False)['risk']['abstain']
    # An OTP floor needs no registry fact; audit must not manufacture a dependence.
    r=evidence.run('credential',.1,True,True,False,False,False)
    assert r['minimal_sufficient_sets']==[[]]


def test_preview_has_no_real_profile_or_log():
    r=client.post('/research/warning-preview',json={'persona':'over_reliant'}).json()
    assert r['kind']=='simulated_profile_comparison'
    assert len(r['conditions'])==3
    assert r['conditions'][0]['warning']['intervention']=='standard'
    assert r['conditions'][1]['warning']['intervention']=='verify_first'
    with reliance._connect() as con:
        assert con.execute('SELECT count(*) FROM decisions').fetchone()[0]==0


def test_pilot_requires_consent_and_balances_assignments():
    assert client.post('/research/pilot/sessions',json={'mode':'pilot','consent':False}).status_code==409
    sessions=[pilot.create('rehearsal',False) for _ in range(3)]
    assert len({s['condition'] for s in sessions})==3
    assert pilot.report(sessions[0]['session_id'])['phases']['transfer']['accuracy'] is None


def test_pilot_sequence_integrity_and_transfer():
    s=pilot.create('rehearsal',False); token=s['session_id']
    with pytest.raises(ValueError):pilot.finish(token,0,'safe',50,'independent_check',1)
    for index in range(9):
        item=next(i for i in pilot.ITEMS if i['id']==s['item']['id'])
        r=pilot.begin(token,index,'safe',60)
        # Retries are idempotent, but initial responses cannot change after advice.
        assert pilot.begin(token,index,'safe',60)==r
        with pytest.raises(ValueError):pilot.begin(token,index,'scam',60)
        if index>=6:
            assert r['warning'] is None and r['ai_advice']=='none'
        if item['planted']:
            assert r['ai_advice']!=item['truth']
        s=pilot.finish(token,index,item['truth'],80,'independent_check',0 if index<6 else None)['next']
        with pytest.raises(ValueError):pilot.finish(token,index,item['truth'],80,'independent_check',0)
    report=pilot.report(token)
    assert report['kind']=='rehearsal' and report['completed']==9
    assert report['phases']['transfer']=={'n':3,'correct':3,'accuracy':1.0}
    assert s['item'] is None and s['debrief']
    with reliance._connect() as con:
        assert con.execute('SELECT count(*) FROM decisions').fetchone()[0]==6


def test_invalid_evidence_score_is_rejected():
    assert client.post('/research/evidence',json={'score':1.5}).status_code==422


def test_irrelevant_matching_fact_does_not_resolve_action_uncertainty():
    from verify.risk import assess
    domain=[{'check':'official_domain','result':'pass','detail':'Copied bank URL'}]
    assert assess(.55,'call',domain)['abstain']
    assert not assess(.55,'call',domain)['action_relevant_support']
    assert not assess(.55,'click',domain)['abstain']


def test_transfer_report_withholds_answers_until_block_complete():
    s=pilot.create('rehearsal',False); token=s['session_id']
    for i in range(7):
        pilot.begin(token,i,'safe',50)
        s=pilot.finish(token,i,'safe',60,'independent_check',0 if i<6 else None)['next']
    report=pilot.report(token)
    assert report['phases']['transfer']['n']==1
    assert report['phases']['transfer']['accuracy'] is None
    transfer=next(r for r in report['rows'] if r['phase']=='transfer')
    assert 'truth' not in transfer and 'correct' not in transfer
