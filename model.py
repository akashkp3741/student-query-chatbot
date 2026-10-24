"""Train an explainable TF-IDF intent classifier using only Python's standard library."""
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STOPWORDS = set('a an the is are am was were be been to of for in on at and or do does did can could would should i me my we our you your please tell about what which how have has it there this that with will must would like where when who'.split())
ALIASES = {'admission': 'admissions', 'apply': 'application', 'applying': 'application',
           'fee': 'fees', 'cost': 'fees', 'costs': 'fees', 'price': 'fees',
           'course': 'courses', 'program': 'courses', 'programs': 'courses',
           'programme': 'courses', 'programmes': 'courses', 'internship': 'internships',
           'placement': 'placements', 'scholarship': 'scholarships', 'hostels': 'hostel',
           'documents': 'document', 'required': 'require', 'requirements': 'require',
           'eligibility': 'eligible', 'companies': 'company', 'recruiters': 'company',
           'deadline': 'date', 'dates': 'date', 'employers': 'company', 'employer': 'company', 'curriculum': 'syllabus'}


def tokenize(text):
    """Normalize a question into comparable, lower-case tokens."""
    return [ALIASES.get(t, t) for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOPWORDS]


def features(text):
    """Return unigram and adjacent-bigram features."""
    words = tokenize(text)
    return words + [a + '_' + b for a, b in zip(words, words[1:])]


def vectorize(text, idf):
    """Create an L2-normalized TF-IDF vector."""
    counts = Counter(features(text))
    vector = {t: (1 + math.log(n)) * idf[t] for t, n in counts.items() if t in idf}
    norm = math.sqrt(sum(v * v for v in vector.values()))
    return {t: v / norm for t, v in vector.items()} if norm else {}


class Chatbot:
    def __init__(self, path=ROOT / 'data' / 'faqs.json'):
        self.data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.intents = {item['id']: item for item in self.data['intents']}
        self.samples = [(q, item['id']) for item in self.intents.values() for q in item['questions']]
        df = Counter(t for q, _ in self.samples for t in set(features(q)))
        self.idf = {t: math.log((1 + len(self.samples)) / (1 + count)) + 1 for t, count in df.items()}
        self.vectors = [(vectorize(q, self.idf), label) for q, label in self.samples]

    def predict(self, message):
        """Return a stable JSON-serializable response for one question."""
        vector = vectorize(message, self.idf)
        scores = {}
        for sample, label in self.vectors:
            similarity = sum(value * sample.get(term, 0) for term, value in vector.items())
            scores[label] = max(scores.get(label, 0), similarity)
        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        best_id, best = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0
        # Penalize questions dominated by words outside the college FAQ vocabulary.
        words = tokenize(message)
        coverage = sum(w in self.idf for w in words) / max(len(words), 1)
        if best < 0.36 or coverage < 0.45 or (best - second < 0.07 and best < 0.88):
            return {'answer': "I couldn't confidently match that question to the FAQ. Try asking one question about admissions, courses, fees, internships, or placements. For a confirmed answer, contact your college office.",
                    'intent': 'fallback', 'category': 'Help', 'score': round(best, 3),
                    'source': 'No reliable FAQ match', 'suggestions': self.data['suggestions'][:3]}
        intent = self.intents[best_id]
        return {'answer': intent['answer'], 'intent': best_id, 'category': intent['category'],
                'score': round(best, 3), 'source': intent['source'],
                'suggestions': intent.get('suggestions', self.data['suggestions'][:3])}

    def export(self, path):
        artifact = {'algorithm': 'TF-IDF word + bigram cosine nearest-example intent classifier',
                    'training_questions': len(self.samples), 'intent_count': len(self.intents),
                    'idf': self.idf, 'vectors': self.vectors}
        Path(path).write_text(json.dumps(artifact, indent=2), encoding='utf-8')

