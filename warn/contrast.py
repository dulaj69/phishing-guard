"""Decision-boundary rehearsal; authored pairs, not a validated learning trial."""
LESSONS = {
 'object': {
  'title':'Same request, different object',
  'a':'Your OTP is ready. Send it to us.',
  'b':'Your receipt is ready. Send it to us.',
  'question':'What changes the credential-disclosure danger?',
  'options':['The greeting','What “it” refers to','The number of sentences'], 'answer':1,
  'explanation':'“Send it” can refer to different objects. Sharing an OTP exposes a credential. A receipt is not an OTP, but can still contain private information; verify the recipient before sharing.',
  'transfer':'Your login code and purchase receipt are ready. Forward that to us.',
  'transfer_options':['Send both','First establish which item is requested; never disclose the login code','The receipt makes the whole message safe'], 'transfer_answer':1},
 'destination': {
  'title':'Same bank name, different destination',
  'a':'Orion Bank: published contact 0112345678. Call 0112345678.',
  'b':'Orion Bank: published contact 0112345678. Call 0771234567.',
  'question':'Which fact must the contact check cover?',
  'options':['Any number in the message','The number the user is asked to call','The bank name alone'], 'answer':1,
  'explanation':'A published number elsewhere in the message cannot verify the requested number. Even an exact match does not authenticate the sender. Use a contact obtained independently.',
  'transfer':'A message includes a known bank website but asks you to call a different, unverified number.',
  'transfer_options':['The website verifies the phone number','Check the requested number using an independent source','A matching logo is sufficient'], 'transfer_answer':1},
 'uncertainty': {
  'title':'Same request, different evidence age',
  'a':'Call 0112345678. In this simulation, its registry entry is current.',
  'b':'Call 0112345678. In this simulation, its registry entry is stale.',
  'question':'What does a stale registry entry establish?',
  'options':['The caller is definitely fraudulent','The destination is definitely safe','Current support is unavailable'], 'answer':2,
  'explanation':'Missing or stale evidence is uncertainty, not proof of fraud or safety. Obtain current independent evidence; a current match still does not authenticate this message.',
  'transfer':'A new bank is absent from the available registry. Its message asks you to call.',
  'transfer_options':['The missing entry proves a scam','Independently verify because registry coverage is missing','Trust it because there is no contradiction'], 'transfer_answer':1},
}


def recommend(binding):
    if binding['clarifications'] or any(a['object'] in ('credential','document')
        for r in binding['requests'] for a in r['alternatives']):
        return 'object'
    if any(not b['used'] and b['reason']=='Different action or destination'
           for r in binding['requests'] for a in r['alternatives'] for b in a['bindings']):
        return 'destination'
    return 'uncertainty'


def item(concept, phase='pair'):
    lesson = LESSONS[concept]
    if phase=='transfer':
        return {'concept':concept,'phase':phase,'text':lesson['transfer'],'options':lesson['transfer_options']}
    return {'concept':concept,'phase':'pair','title':lesson['title'], 'a':lesson['a'],'b':lesson['b'],
            'question':lesson['question'],'options':lesson['options']}


def answer(concept, phase, choice):
    lesson = LESSONS[concept]
    return {'correct':choice==lesson['transfer_answer' if phase=='transfer' else 'answer'],
            'explanation':lesson['explanation'], 'kind':'rehearsal_feedback_not_study_evidence',
            'next':item(concept,'transfer') if phase=='pair' else None}
