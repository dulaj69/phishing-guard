import pytest
from fastapi.testclient import TestClient
from api.main import app
from detection.context import resolve
from research.lab.decision_boundary import run, benchmark
from verify.binding import evaluate
from warn.contrast import item


def turns(*text):
    return [{'speaker':'sender','text':t} for t in text]


def test_split_reference_has_real_normalized_source_offsets():
    g=resolve(turns('Your O T P is ready.','Send it.'))
    node=g['requests'][0]
    h=node['interpretations'][0]
    assert h['action']=='share_credential'
    a=h['antecedents'][0]
    assert g['turns'][a['turn']]['text'][a['start']:a['end']]==a['text']=='OTP'


def test_ambiguous_request_carries_alternatives_then_explicit_user_clarification():
    t=turns('Your OTP and receipt are ready.','Send it.')
    r=run(t)
    q=r['verification']['clarifications'][0]
    assert q['options']==['credential','document','not_sure']
    assert r['verification']['requests'][0]['tier_range']==['Medium','High']
    selected=run(t,clarification={'request_id':q['request_id'],'object':'document'})
    assert not selected['verification']['clarifications']
    assert selected['detection']['requests'][0]['resolution']=='user_clarified_not_verified'
    assert selected['before_clarification']['clarifications']
    assert run(t,clarification={'request_id':q['request_id'],'object':'not_sure'})['verification']['clarifications']
    with pytest.raises(ValueError):run(t,clarification={'request_id':'fake','object':'document'})


def test_negation_report_and_recipient_request_do_not_become_sender_requests():
    for message in ['Never send it.','Someone asked me to send it.']:
        assert not run(turns('Your OTP is ready.',message))['verification']['requests']
    t=turns('Your OTP is ready.')+[{'speaker':'recipient','text':'Share your OTP.'}]
    assert not run(t)['verification']['requests']


def test_contact_match_cannot_be_reused_for_another_destination():
    r=run(turns('Published number 0112345678. Call 0771234567.'))
    a=r['verification']['requests'][0]['alternatives'][0]
    assert a['destination']=='0771234567'
    assert a['risk']['abstain'] and not a['risk']['action_relevant_support']
    assert not r['type_only_comparator'][0]['risk']['abstain']
    assert r['learning']['concept']=='destination'


def test_exact_route_stale_and_missing_have_distinct_coverage():
    t=turns('Call 0112345678.')
    assert not run(t)['verification']['requests'][0]['alternatives'][0]['risk']['abstain']
    for mode in ['stale','missing']:
        assert run(t,mode)['verification']['requests'][0]['alternatives'][0]['risk']['abstain']


def test_unaccepted_provenance_cannot_resolve_uncertainty():
    g=resolve(turns('Call 0112345678.'))
    fact={'id':'f','action':'call','destination':'0112345678','fresh':True,'provenance':'user_claim',
          'result':'pass','detail':'Untrusted assertion'}
    assert evaluate(g,[fact])['requests'][0]['alternatives'][0]['risk']['abstain']


def test_credential_warning_not_overridden_by_matching_phone():
    r=run(turns('Send your OTP. Call 0112345678.'),score=.01)
    h=next(a for n in r['verification']['requests'] for a in n['alternatives'] if a['action']=='share_credential')
    assert h['risk']['tier']=='High' and h['recommendation']=='do_not_share'


def test_development_benchmark_keeps_known_failures_visible():
    b=benchmark()
    assert b['extension_correct']<b['n']
    assert any(not r['extension_correct'] and r['id']=='unseen-synonym' for r in b['rows'])


def test_exercise_does_not_disclose_answers_before_response():
    for concept in ['object','destination','uncertainty']:
        for phase in ['pair','transfer']:
            assert not any('answer' in key for key in item(concept,phase))


def test_boundary_requires_account_and_enforces_limits(temp_reliance_db):
    with TestClient(app) as c:
        assert c.get('/research/boundary/catalog').status_code==401
        c.headers['X-Research-Request']='1'
        assert c.post('/account/signup',json={'username':'boundarytest','password':'a secure test passphrase'}).status_code==201
        assert c.get('/app/lab/boundary.html').status_code==200
        assert c.post('/research/boundary/analyze',json={'turns':turns('Send your OTP.')}).status_code==200
        assert c.post('/research/boundary/analyze',json={'turns':turns(*['x']*7)}).status_code==422
        assert c.post('/research/boundary/analyze',json={'turns':turns('x'),'score':2}).status_code==422
        assert c.post('/research/boundary/answer',json={'concept':'object','phase':'pair','choice':1}).json()['correct']
        assert c.post('/research/boundary/answer',json={'concept':'object','phase':'pair','choice':9}).status_code==422
