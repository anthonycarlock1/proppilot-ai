"""Urgency development baseline. Synthetic evaluation is not safety validation."""
import csv
import hashlib
import json
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
LABELS = ['low', 'medium', 'high', 'emergency']


def load_data(path):
    with path.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    seen_ids, seen_text, groups = set(), set(), {}
    for row in rows:
        if row['urgency'] not in LABELS or row['split'] not in {'train', 'test'}:
            raise ValueError('Invalid urgency or split')
        text = ' '.join(row['text'].lower().split())
        if not text or row['id'] in seen_ids or text in seen_text:
            raise ValueError('Empty text or duplicate example')
        group = row['scenario_group']
        if not group or (group in groups and groups[group] != row['split']):
            raise ValueError('Missing group or scenario group crosses partitions')
        groups[group] = row['split']
        seen_ids.add(row['id'])
        seen_text.add(text)
    for split in ('train', 'test'):
        if {r['urgency'] for r in rows if r['split'] == split} != set(LABELS):
            raise ValueError('Every partition must contain all urgency labels')
    return rows


def main():
    path = ROOT / 'ml/data/urgency_seed.csv'
    rows = load_data(path)
    train = [r for r in rows if r['split'] == 'train']
    test = [r for r in rows if r['split'] == 'test']
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)),
    ])
    model.fit([r['text'] for r in train], [r['urgency'] for r in train])
    predicted = model.predict([r['text'] for r in test])
    report = classification_report([r['urgency'] for r in test], predicted,
                                   labels=LABELS, output_dict=True, zero_division=0)
    predictions = [dict(id=r['id'], text=r['text'], expected=r['urgency'], predicted=str(p),
                        priority_steps_under=max(0, LABELS.index(r['urgency']) - LABELS.index(str(p))))
                   for r, p in zip(test, predicted)]
    result = {
        'dataset': str(path.relative_to(ROOT)),
        'dataset_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'data_origin': 'AI-authored synthetic seed; human review pending',
        'limitations': 'Tiny synthetic holdout, with related issue types across splits; not evidence of real-world reliability or emergency detection safety. Do not tune against this holdout.',
        'sklearn_version': sklearn.__version__,
        'train_count': len(train), 'test_count': len(test), 'labels': LABELS,
        'classification_report': report,
        'emergency_recall': report['emergency']['recall'],
        'under_prioritized_count': sum(p['priority_steps_under'] > 0 for p in predictions),
        'severely_under_prioritized_count': sum(p['priority_steps_under'] >= 2 for p in predictions),
        'confusion_matrix': confusion_matrix([r['urgency'] for r in test], predicted, labels=LABELS).tolist(),
        'predictions': predictions,
    }
    artifact_dir = ROOT / 'ml/artifacts'
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / 'urgency-v0.1.0.joblib')
    output = ROOT / 'ml/evaluation/urgency-baseline.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Train: {len(train)}; test: {len(test)}')
    print(f"Synthetic holdout macro F1: {report['macro avg']['f1-score']:.3f}")
    print(f"Emergency recall: {result['emergency_recall']:.3f}")
    print(f"Under-prioritized: {result['under_prioritized_count']}; severe: {result['severely_under_prioritized_count']}")
    for p in predictions:
        if p['expected'] != p['predicted']:
            print(f"Mismatch: {p['id']} expected={p['expected']} predicted={p['predicted']}")


if __name__ == '__main__':
    main()
