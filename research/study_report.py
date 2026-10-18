"""Summarize exported study decisions by participant, session and condition.

python -m research.study_report decisions.csv --output study_summary.json
Reports denominators; does not treat repeated trials as independent participants.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def summarize(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r['user_id'], r.get('session', ''), r.get('condition', ''))].append(r)
    output = []
    for (user, session, condition), trials in grouped.items():
        labelled = [r for r in trials if r.get('truth') in ('scam', 'safe')]
        opportunities = [r for r in labelled if r.get('initial_choice') in ('scam', 'safe')
                         and r['ai_advice'] in ('scam', 'safe') and r['initial_choice'] != r['ai_advice']]
        rair = [r for r in opportunities if r['ai_advice'] == r['truth']]
        rsr = [r for r in opportunities if r['initial_choice'] == r['truth']]
        scams = [r for r in labelled if r['truth'] == 'scam']
        times = [float(r['seconds']) for r in labelled if r.get('seconds') not in (None, '')]
        rate = lambda n, d: n / d if d else None
        output.append({'user_id': user, 'session': session, 'condition': condition,
                       'n': len(labelled), 'accuracy': rate(sum(r['final_choice'] == r['truth'] for r in labelled), len(labelled)),
                       'RAIR_n': len(rair), 'RAIR': rate(sum(r['final_choice'] == r['truth'] for r in rair), len(rair)),
                       'RSR_n': len(rsr), 'RSR': rate(sum(r['final_choice'] == r['truth'] for r in rsr), len(rsr)),
                       'scam_trials': len(scams),
                       'unsafe_action_rate': rate(sum((r.get('action') or '').split(':')[0] in ('call_sms_number', 'open_link', 'verify_first_wrong') for r in scams), len(scams)),
                       'mean_seconds': mean(times) if times else None,
                       'abstentions': sum(r['ai_advice'] == 'uncertain' for r in labelled)})
    return {'participants': len({r['user_id'] for r in rows}), 'participant_sessions': output,
            'limitations': 'Descriptive pilot summaries; no causal or significance claim. Pre-register assignment and sample size before formal study.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decisions'); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with open(args.decisions, newline='') as f:
        result = summarize(list(csv.DictReader(f)))
    Path(args.output).write_text(json.dumps(result, indent=2, allow_nan=False))
