"""Score frozen trusted local baselines without training or changing deployed models."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

import joblib
import sklearn
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
LABELS = {'category': ['hvac', 'plumbing', 'electrical', 'general'],
          'urgency': ['low', 'medium', 'high', 'emergency']}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def normalize(text):
    return re.sub(r'\W+', ' ', text.casefold()).strip()


def main():
    case_path = ROOT / 'ml/data/challenge-v1.csv'
    unscored_path = ROOT / 'ml/data/challenge-unscored-v1.csv'
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', str(case_path), str(unscored_path),
                    str(ROOT / 'ml/evaluation/challenge-protocol.md')], cwd=ROOT, check=True, capture_output=True)
    cases, unscored = read(case_path), read(unscored_path)
    if len(cases) != 32 or len(unscored) != 8:
        raise ValueError('Unexpected v1 suite size')
    all_cases = cases + unscored
    if len({r['id'] for r in all_cases}) != len(all_cases) or len({normalize(r['text']) for r in all_cases}) != len(all_cases):
        raise ValueError('Duplicate IDs or normalized text')
    for task, labels in LABELS.items():
        if any(sum(r[task] == label for r in cases) != 8 for label in labels):
            raise ValueError('Expected balanced labels')
    seeds = {task: read(ROOT / f'ml/data/{task}_seed.csv') for task in LABELS}
    seen = {normalize(r['text']) for rows in seeds.values() for r in rows}
    if any(normalize(r['text']) in seen for r in all_cases):
        raise ValueError('Exact normalized overlap with seed data')
    result = {'suite_version': 1, 'suite_frozen_commit': subprocess.check_output(
        ['git', 'log', '-1', '--format=%H', '--', 'ml/data/challenge-v1.csv'], cwd=ROOT, text=True).strip(),
        'data_origin': 'Additional AI-authored synthetic diagnostic suite; human case-label review pending',
        'human_review_snapshot': json.loads((ROOT / 'ml/evaluation/review-status.json').read_text()),
        'limitations': ['Not independently authored, blind, representative or safety validation',
                       'Created after known baseline errors; includes targeted weaknesses',
                       'Probabilities are uncalibrated; unsupported cases have no scored labels',
                       'Local artifacts are not asserted byte-identical to separate cloud builds'],
        'case_sha256': sha(case_path), 'unscored_sha256': sha(unscored_path),
        'scored_count': len(cases), 'unscored_count': len(unscored), 'sklearn_version': sklearn.__version__,
        'exact_seed_overlap': False, 'production_acceptance': 'No agreed threshold; diagnostic only', 'tasks': {}}
    for task, labels in LABELS.items():
        artifact = ROOT / f'ml/artifacts/{task}-v0.1.0.joblib'
        before = sha(artifact)
        model = joblib.load(artifact)  # Only trusted project-produced artifacts.
        original = json.loads((ROOT / f'ml/evaluation/{task}-baseline.json').read_text())
        if sha(ROOT / f'ml/data/{task}_seed.csv') != original['dataset_sha256']:
            raise ValueError('Seed data changed from recorded baseline')
        holdout = {r['id']: r for r in seeds[task] if r['split'] == 'test'}
        for prediction in original['predictions']:
            actual = str(model.predict([holdout[prediction['id']]['text']])[0])
            if actual != prediction['predicted']:
                raise ValueError('Local artifact no longer reproduces original holdout predictions')
        predicted = model.predict([r['text'] for r in cases])
        probabilities = model.predict_proba([r['text'] for r in cases])
        train = [r for r in seeds[task] if r['split'] == 'train']
        vectorizer = model.named_steps['tfidf']
        similarity = cosine_similarity(vectorizer.transform([r['text'] for r in cases]),
                                       vectorizer.transform([r['text'] for r in train]))
        predictions = []
        for row, prediction, probability, sim in zip(cases, predicted, probabilities, similarity):
            nearest = int(sim.argmax())
            item = {'id': row['id'], 'text': row['text'], 'expected': row[task], 'predicted': str(prediction),
                    'max_uncalibrated_probability': float(max(probability)),
                    'nearest_training_id': train[nearest]['id'], 'nearest_training_cosine': float(sim[nearest])}
            if task == 'urgency':
                item['priority_steps_under'] = max(0, labels.index(row[task]) - labels.index(str(prediction)))
            predictions.append(item)
        metrics = classification_report([r[task] for r in cases], predicted, labels=labels, output_dict=True, zero_division=0)
        unsupported_predictions = model.predict([r['text'] for r in unscored])
        unsupported_probabilities = model.predict_proba([r['text'] for r in unscored])
        task_result = {'labels': labels, 'artifact_sha256': before, 'original_holdout_predictions_reproduced': True,
            'classification_report': metrics,
            'confusion_matrix': confusion_matrix([r[task] for r in cases], predicted, labels=labels).tolist(),
            'predictions': predictions,
            'unscored_outputs': [dict(row, predicted=str(prediction), max_uncalibrated_probability=float(max(probability)))
                for row, prediction, probability in zip(unscored, unsupported_predictions, unsupported_probabilities)]}
        if task == 'urgency':
            task_result.update(emergency_recall=metrics['emergency']['recall'],
                missed_emergency_ids=[r['id'] for r in predictions if r['expected'] == 'emergency' and r['predicted'] != 'emergency'],
                under_prioritized_count=sum(r['priority_steps_under'] > 0 for r in predictions),
                severely_under_prioritized_count=sum(r['priority_steps_under'] >= 2 for r in predictions))
        if sha(artifact) != before:
            raise RuntimeError('Artifact changed during evaluation')
        result['tasks'][task] = task_result
        print(f"{task}: accuracy={metrics['accuracy']:.3f}; macro F1={metrics['macro avg']['f1-score']:.3f}")
        if task == 'urgency':
            print(f"Emergency recall={task_result['emergency_recall']:.3f}; under-priority={task_result['under_prioritized_count']}; severe={task_result['severely_under_prioritized_count']}")
    output = ROOT / 'ml/evaluation/challenge-v1-results.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print('Saved complete results; artifacts and deployed endpoints unchanged.')


if __name__ == '__main__':
    main()
