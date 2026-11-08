"""API surface for bounded research demonstrations."""
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Depends
from api import accounts
from pydantic import BaseModel, Field
from research.lab import robustness, evidence, pilot
from research.lab.cases import CASES

router = APIRouter(prefix='/research', tags=['Research workbench'], dependencies=[Depends(accounts.current)])


def guarded(fn):
    try:
        return fn()
    except ValueError as e:
        raise HTTPException(409,str(e))
    except FileNotFoundError:
        raise HTTPException(503,'Train the local classifier before running this experiment.')


@router.get('/catalog')
def catalog():
    return {'cases':CASES,'model_fingerprint':guarded(robustness.fingerprint),
            'fixture_status':'Authored diagnostic cases, not a held-out test set; Sinhala/Singlish await native review.',
            'contributions':[
                {'owner':'Sanmith','title':'Action contrast & language robustness','question':'Does meaning-preserving variation preserve actions while negation changes them?',
                 'built':'Diagnostic variants, keyword comparator, contextual extraction and executable benchmark.',
                 'remaining':'Human-adjudicated local gold set; train joint model; evaluate unseen campaigns.'},
                {'owner':'Perera','title':'Evidence dependency & uncertainty','question':'Which facts are sufficient for a risk decision, and what happens when evidence disappears?',
                 'built':'Controlled evidence interventions, baseline comparisons and exact subset audit.',
                 'remaining':'Reviewed real bank registry, expert rankings and threshold validation.'},
                {'owner':'Rathnayake','title':'Adaptive learning, reliance & transfer','question':'Do warnings support correct independent decisions after advice is removed?',
                 'built':'Three-condition warning pilot plus private misconception-targeted learning, static comparison, confidence and reason measures, immediate transfer and a 24-hour follow-up gate.',
                 'remaining':'Expert-reviewed multilingual instruments, approved study protocol, sample-size justification, recruitment and actual delayed observations.'}]}


class CaseRequest(BaseModel):
    case_id: str = Field(max_length=80)


@router.post('/robustness')
def inspect(req:CaseRequest):
    return guarded(lambda:robustness.inspect(req.case_id))


@router.post('/benchmark')
def benchmark():
    return guarded(robustness.benchmark)


class EvidenceRequest(BaseModel):
    scenario: Literal['callback','credential','link']='callback'
    score: float = Field(.55, ge=0, le=1, allow_inf_nan=False)
    contradiction: bool = True
    copied_domain: bool = True
    stale: bool = False
    missing: bool = False
    uncertainty: bool = False


@router.post('/evidence')
def audit(req:EvidenceRequest):
    return evidence.run(**req.model_dump())


class SessionRequest(BaseModel):
    mode: Literal['rehearsal','pilot']='rehearsal'
    consent: bool=False


@router.post('/pilot/sessions')
def create(req:SessionRequest,user=Depends(accounts.current)):
    result = guarded(lambda:pilot.create(req.mode,req.consent))
    with accounts.connect() as con:
        con.execute('INSERT INTO pilot_owners VALUES (?,?)',(result['session_id'],user['id']))
    return result


class Initial(BaseModel):
    index:int=Field(ge=0,le=8)
    choice:Literal['safe','scam']
    confidence:int=Field(ge=0,le=100)


class Final(Initial):
    action:Literal['independent_check','follow_sms','ignore_report']
    comprehension:Optional[int]=Field(None,ge=0,le=2)


@router.get('/pilot/{token}')
def get_session(token:str,user=Depends(accounts.current)):
    accounts.own_pilot(token,user)
    return guarded(lambda:pilot.status(token))


@router.post('/pilot/{token}/initial')
def initial(token:str,req:Initial,user=Depends(accounts.current)):
    accounts.own_pilot(token,user)
    return guarded(lambda:pilot.begin(token,**req.model_dump()))


@router.post('/pilot/{token}/final')
def final(token:str,req:Final,user=Depends(accounts.current)):
    accounts.own_pilot(token,user)
    return guarded(lambda:pilot.finish(token,**req.model_dump()))


@router.get('/pilot/{token}/report')
def report(token:str,user=Depends(accounts.current)):
    accounts.own_pilot(token,user)
    return guarded(lambda:pilot.report(token))


class WarningPreview(BaseModel):
    case_id: str = 'otp-en'
    persona: Literal['new','over_reliant','under_reliant','balanced']='over_reliant'


@router.post('/warning-preview')
def preview(req:WarningPreview):
    from detection.model import detect
    from verify.service import verify
    from warn import reliance
    from warn.composer import compose
    from research.lab.cases import case
    def run():
        c=case(req.case_id)
        d=detect([c['text']])[0]; v=verify(d)
        profile={'intervention':{'new':'standard','over_reliant':'verify_first','under_reliant':'strong_evidence','balanced':'light'}[req.persona]}
        return {'kind':'simulated_profile_comparison','persona':req.persona,'text':c['text'],
                'evidence_quality':v['risk']['evidence_quality'],
                'conditions':[{'condition':condition,'warning':compose(d,v,'en',reliance.choose_warning(profile,v['risk'],condition))}
                              for condition in pilot.CONDITIONS],
                'limitation':'Profiles are selected simulations, not measured participants. No decisions are logged.'}
    return guarded(run)

# Experimental extensions: bounded context, exact evidence binding, contrast rehearsal.
from research.lab import decision_boundary
from warn import contrast

class ContextTurn(BaseModel):
    speaker: Literal['sender','recipient']='sender'
    text: str = Field(min_length=1,max_length=2000)

class Clarification(BaseModel):
    request_id: str = Field(max_length=80)
    object: Literal['credential','document','not_sure']

class BoundaryRequest(BaseModel):
    turns: list[ContextTurn] = Field(min_length=1,max_length=6)
    evidence_mode: Literal['current','stale','missing']='current'
    score: float = Field(.55,ge=0,le=1,allow_inf_nan=False)
    clarification: Optional[Clarification]=None

@router.get('/boundary/catalog')
def boundary_catalog():
    return {'fixtures':decision_boundary.FIXTURES}

@router.post('/boundary/analyze')
def boundary_analyze(req:BoundaryRequest):
    return guarded(lambda:decision_boundary.run(**req.model_dump()))

@router.post('/boundary/benchmark')
def boundary_benchmark():
    return decision_boundary.benchmark()

class ContrastAnswer(BaseModel):
    concept: Literal['object','destination','uncertainty']
    phase: Literal['pair','transfer']
    choice: int = Field(ge=0,le=2)

@router.post('/boundary/answer')
def boundary_answer(req:ContrastAnswer):
    return contrast.answer(**req.model_dump())
