"""Train and evaluate a synthetic-data baseline; run from any directory."""
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
LABELS = ['hvac', 'plumbing', 'electrical', 'general']


def load_data(path):
    with path.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    seen_ids, seen_text, groups = set(), set(), {}
    for row in rows:
        if row['category'] not in LABELS or row['split'] not in {'train', 'test'}:
            raise ValueError('Invalid category or split')
        normalized = ' '.join(row['text'].lower().split())
        if not normalized or row['id'] in seen_ids or normalized in seen_text:
            raise ValueError('Empty text or duplicate example')
        if not row['scenario_group']:
            raise ValueError('Missing scenario group')
        group = row['scenario_group']
        if group in groups and groups[group] != row['split']:
            raise ValueError('Scenario group crosses train/test partitions')
        groups[group] = row['split']
        seen_ids.add(row['id'])
        seen_text.add(normalized)
    for split in ('train', 'test'):
        if {r['category'] for r in rows if r['split'] == split} != set(LABELS):
            raise ValueError('Every partition must contain every category')
    return rows


def main():
    path = ROOT / 'ml/data/category_seed.csv'
    rows = load_data(path)
    train = [r for r in rows if r['split'] == 'train']
    test = [r for r in rows if r['split'] == 'test']
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)),
    ])
    model.fit([r['text'] for r in train], [r['category'] for r in train])
    predicted = model.predict([r['text'] for r in test])
    report = classification_report([r['category'] for r in test], predicted,
                                   labels=LABELS, output_dict=True, zero_division=0)
    result = {
        'dataset': str(path.relative_to(ROOT)),
        'dataset_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'data_origin': 'AI-authored synthetic seed; human review pending',
        'limitations': 'Small synthetic holdout; not evidence of real-world reliability. Do not tune against this holdout.',
        'sklearn_version': sklearn.__version__,
        'train_count': len(train), 'test_count': len(test), 'labels': LABELS,
        'classification_report': report,
        'confusion_matrix': confusion_matrix([r['category'] for r in test], predicted, labels=LABELS).tolist(),
        'predictions': [dict(id=r['id'], text=r['text'], expected=r['category'], predicted=str(p))
                        for r, p in zip(test, predicted)],
    }
    artifact_dir = ROOT / 'ml/artifacts'
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / 'category-v0.1.0.joblib')
    output = ROOT / 'ml/evaluation/category-baseline.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Train: {len(train)}; test: {len(test)}')
    print(f"Synthetic holdout macro F1: {report['macro avg']['f1-score']:.3f}")
    for row, prediction in zip(test, predicted):
        if row['category'] != prediction:
            print(f"Mismatch: {row['id']} expected={row['category']} predicted={prediction}")
    print(f'Evaluation: {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
