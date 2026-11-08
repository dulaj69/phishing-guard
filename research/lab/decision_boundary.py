"""Three component integration and transparent development fixtures.

Deliberately separate from the frozen public detector. All source evidence below
is fictional. Custom text is ephemeral; no learned performance claims are made.
"""
from detection.context import resolve
from detection.anatomy import extract
from detection.preprocess import clean
from verify.binding import evaluate, clarify
from verify.risk import assess
from warn import contrast

FIXTURES = [
 {'id':'split-otp','name':'OTP request split across messages','turns':['Your OTP is ready.','Send it to us.'],'expected':['share_credential']},
 {'id':'split-receipt','name':'Document request split across messages','turns':['Your receipt is ready.','Send it to us.'],'expected':['reply']},
 {'id':'ambiguous','name':'Two possible objects','turns':['Your OTP and receipt are ready.','Send it to us.'],'expected':['reply','share_credential']},
 {'id':'singlish','name':'Mixed-language reference (review needed)','turns':['obe OTP eka apita godak wadagath, share it'],'expected':['share_credential']},
 {'id':'negation','name':'Do not share','turns':['Your OTP is ready.','Never send it to us.'],'expected':[]},
 {'id':'reported','name':'Reported request','turns':['Your OTP is ready.','Someone asked me to send it.'],'expected':[]},
 {'id':'route-swap','name':'Published number beside a different requested number','turns':['Orion Bank: published number 0112345678. Call 0771234567.'],'expected':['call']},
 {'id':'exact-route','name':'Exact requested number match','turns':['Orion Bank: call 0112345678.'],'expected':['call']},
 {'id':'unseen-synonym','name':'Known limitation: unseen credential synonym','turns':['Your authentication secret is ready.','Send it to us.'],'expected':['share_credential']},
 {'id':'unseen-reference','name':'Known limitation: indirect reference','turns':['Your OTP is ready.','Pass the above to us.'],'expected':['share_credential']},
 {'id':'reported-variant','name':'Known limitation: quotation scope','turns':['Your OTP is ready.','The caller said send it to us.'],'expected':[]},
 {'id':'unresolved','name':'Missing antecedent','turns':['Send it to us.'],'expected':[]},
]


def facts(mode):
    if mode=='missing':
        return []
    return [{'id':'published-number','action':'call','destination':'0112345678',
             'result':'pass','fresh':mode!='stale','provenance':'curated_fixture',
             'source':'https://orionbank.example/contacts','fictional':True,
             'detail':'Fictional published contact; simulation only, no real verification.'}]


def run(turns, evidence_mode='current', score=.55, clarification=None):
    graph = resolve(turns)
    before = evaluate(graph,facts(evidence_mode),score)
    if clarification:
        graph = clarify(graph,clarification['request_id'],clarification['object'])
    bound = evaluate(graph,facts(evidence_mode),score)
    # Comparator deliberately reproduces the older check-type-only policy.
    loose = []
    for r in bound['requests']:
        for h in r['alternatives']:
            checks=[{'check':'official_number','result':'pass' if f['fresh'] else 'unknown','detail':f['detail']} for f in facts(evidence_mode)]
            loose.append({'action':h['action'],'destination':h.get('destination'),
                          'risk':assess(score,h['action'],checks)})
    concept = contrast.recommend(bound)
    return {'kind':'development_rehearsal','detection':graph,'verification':bound,
            'before_clarification':before if clarification else None,
            'type_only_comparator':loose, 'learning':contrast.item(concept),
            'controlled_score':score,
            'limitation':'The score is manually controlled, not a new model prediction. Evidence is fictional. These are research extensions, not validated novelty or measured learning gains. No messages or answers are saved.'}


def benchmark():
    rows=[]
    for f in FIXTURES:
        turns=[{'speaker':'sender','text':t} for t in f['turns']]
        result=resolve(turns)
        got=sorted({h['action'] for n in result['requests'] if n['status']=='requested' for h in n['interpretations'] if h['action']!='none'})
        # Compare same task: requested action set, not just primary action.
        last=extract(clean(f['turns'][-1])[0])
        joined=extract(clean(' '.join(f['turns']))[0])
        baseline=lambda d:sorted({e['action'] for e in d['action_evidence'] if e['status']=='requested'})
        expected=sorted(f['expected'])
        rows.append({'id':f['id'],'expected':expected,'last_message':baseline(last),
                     'concatenated':baseline(joined),'hypotheses':got,
                     'last_correct':baseline(last)==expected,'concat_correct':baseline(joined)==expected,
                     'extension_correct':got==expected})
    return {'kind':'authored_development_diagnostic','n':len(rows),'rows':rows,
            'last_correct':sum(r['last_correct'] for r in rows),'concat_correct':sum(r['concat_correct'] for r in rows),
            'extension_correct':sum(r['extension_correct'] for r in rows),
            'limitation':'Fixtures designed alongside implementation; exact-set matches are not generalization accuracy. Ambiguity set evaluation favours a set-returning interface; separately evaluate singleton coverage and unsafe commitments on independent data.'}
