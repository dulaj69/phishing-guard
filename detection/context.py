"""Bounded, inspectable reference hypotheses; not a general coreference model.

Offsets refer to normalized turns. Earlier sender clauses supply candidate objects;
recipient speech never becomes a sender request. No text is persisted here.
"""
import re
from detection.preprocess import clean
from detection.anatomy import extract, NEGATION, REPORTED, ACTION_WORDS

OBJECTS = {
    'credential': ACTION_WORDS['share_credential']['terms'],
    'document': r'\b(receipt|invoice|statement|document)\b',
}
SEND = re.compile(ACTION_WORDS['share_credential']['verbs'], re.I)
REFERENCE = re.compile(r'\b(it|that|this|them|eka|meka)\b|ඒක|එය', re.I)
CLAUSE = re.compile(r'[^,;.!?\n]+(?:[.!?](?!\s|$)[^,;.!?\n]*)*')


def resolve(turns):
    normalized, nodes, history = [], [], []
    for turn_index, turn in enumerate(turns):
        text, language, changes = clean(turn['text'])
        normalized.append({'speaker':turn['speaker'], 'text':text, 'language':language, 'changes':changes})
        if turn['speaker'] != 'sender':
            continue
        # Only reference-bearing send clauses use this experimental extension.
        for match in CLAUSE.finditer(text):
            clause = match.group()
            objects = []
            for kind, pattern in OBJECTS.items():
                for m in re.finditer(pattern, clause, re.I):
                    objects.append({'kind':kind, 'turn':turn_index, 'start':match.start()+m.start(),
                                    'end':match.start()+m.end(), 'text':m.group()})
            status = 'negated' if NEGATION.search(clause) else 'reported' if REPORTED.search(clause) else 'requested'
            if SEND.search(clause) and (objects or REFERENCE.search(clause)):
                pool = objects or [obj for group in history[-3:] for obj in group]
                kinds = sorted({o['kind'] for o in pool}) or ['unknown']
                nodes.append({'id':f't{turn_index}-c{match.start()}', 'turn':turn_index,
                              'text':clause.strip(), 'status':status,
                              'start':match.start(), 'end':match.end(),
                              'resolution':'explicit' if objects else 'bounded_reference',
                              'interpretations':[{'object':kind,
                                  'action':'share_credential' if kind=='credential' else 'reply' if kind=='document' else 'none',
                                  'antecedents':[o for o in pool if o['kind']==kind]} for kind in kinds]})
            history.append(objects)
        # Existing extraction handles non-send actions, with target scoped to its evidence clause.
        for e in extract(text)['action_evidence']:
            if e['action'] in ('share_credential','reply'):
                continue
            local = extract(e['text'])
            wanted = 'url' if e['action']=='click' else 'phone' if e['action']=='call' else None
            targets = [c for c in local['contacts'] if c['type']==wanted or (wanted=='phone' and c['type']=='short_code')]
            nodes.append({'id':f't{turn_index}-{e["action"]}-{e["start"]}', 'turn':turn_index,
                          'text':e['text'], 'start':e['start'], 'end':e['end'], 'status':e['status'],
                          'resolution':'explicit', 'interpretations':[{'object':wanted or 'unknown',
                          'action':e['action'], 'destination':c['normalized'], 'antecedents':[]} for c in targets]
                          or [{'object':'unknown','action':e['action'],'antecedents':[]}]})
    return {'method':'bounded_reference_hypotheses_v1', 'turns':normalized, 'requests':nodes,
            'limitation':'Programmed patterns; last three sender clauses only. No general coreference, speaker authentication or calibrated uncertainty. English and limited Sinhala/Singlish patterns need independent native review.'}
