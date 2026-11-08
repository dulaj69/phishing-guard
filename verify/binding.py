"""Experimental action/destination evidence binding and uncertainty propagation.

Input evidence is curated by the lab, never accepted as verified user assertions.
A match means only a matching published destination, not authentic sender or intent.
"""
from verify.risk import assess, TIERS


def evaluate(graph, facts, score=.55):
    rows, questions = [], []
    for node in graph['requests']:
        if node['status'] != 'requested':
            continue
        alternatives = []
        for h in node['interpretations']:
            binding = []
            checks = []
            for fact in facts:
                same = fact['action']==h['action'] and bool(h.get('destination')) and fact['destination']==h.get('destination')
                usable = same and fact['fresh'] and fact['provenance']=='curated_fixture'
                binding.append({'id':fact['id'], 'used':usable,
                                'reason':'Exact action and destination match' if usable else
                                         'Stale source' if same and not fact['fresh'] else
                                         'Unaccepted provenance' if same else 'Different action or destination'})
                if usable:
                    checks.append({'check':'official_number' if h['action']=='call' else 'official_domain',
                                   'result':fact['result'],'detail':fact['detail']})
            risk = assess(score,h['action'],checks,'uncertain' if h['object']=='unknown' else 'rule_based')
            recommendation = ('do_not_share' if h['action']=='share_credential' else
                              'clarify_object' if h['object']=='unknown' and h['action']=='none' else
                              'verify_independently')
            alternatives.append({**h, 'risk':risk, 'recommendation':recommendation, 'bindings':binding})
        tiers = [a['risk']['tier'] for a in alternatives]
        ambiguous = len(alternatives)>1 or any(a['object']=='unknown' for a in alternatives)
        changes = len({(a['risk']['tier'],a['recommendation']) for a in alternatives})>1
        question = ambiguous and (changes or any(a['recommendation']=='clarify_object' for a in alternatives))
        if question:
            questions.append({'request_id':node['id'],
                              'text':'What does “it/that” refer to? Select a type; never enter the actual code or document.',
                              'options':list(dict.fromkeys([a['object'] for a in alternatives if a['object']!='unknown']+['not_sure']))})
        rows.append({'request_id':node['id'], 'text':node['text'], 'alternatives':alternatives,
                     'tier_range':[min(tiers,key=TIERS.index),max(tiers,key=TIERS.index)],
                     'ambiguous':ambiguous, 'decision_sensitive':changes, 'question_needed':question})
    return {'method':'exact_destination_binding_v1', 'requests':rows, 'clarifications':questions,
            'policy':'No published detail authenticates the sender. Ambiguous interpretations remain visible; no probabilities assigned.',
            'facts':facts}


def clarify(graph, request_id, object_type):
    """Explicit user clarification is labelled, not promoted to external evidence."""
    import copy
    result = copy.deepcopy(graph)
    node = next((n for n in result['requests'] if n['id']==request_id and n['status']=='requested'),None)
    if node is None:
        raise ValueError('Unknown requested action')
    if object_type=='not_sure':
        return result
    matches = [h for h in node['interpretations'] if h['object']==object_type]
    if not matches:
        raise ValueError('Choose one of the displayed object types')
    node['interpretations']=matches
    node['resolution']='user_clarified_not_verified'
    return result
