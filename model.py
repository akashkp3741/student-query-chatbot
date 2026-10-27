"""TF-IDF intent classifier for the CampusGuide student query chatbot.

Project owner: Nayana K C

The model is a small, explainable nearest-example classifier built only with
Python's standard library:

1. Every training question in ``data/faqs.json`` is tokenized, normalized and
   turned into unigram + bigram features.
2. Smoothed inverse document frequency (IDF) weights are fitted over those
   training questions.
3. Each training question becomes an L2-normalized TF-IDF vector.
4. At prediction time the student's message is vectorized the same way and
   compared with every training vector using cosine similarity. The intent
   with the best-matching example wins, unless one of the safety gates in
   ``Chatbot.predict`` rejects the match, in which case a fallback is returned.

This is not a generative model: answers are always taken from the curated FAQ
file, so the bot never invents college facts.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

# Folder that contains this file; used to locate data/ and model.json.
ROOT = Path(__file__).resolve().parent

# Very common words that carry no intent information and are dropped.
STOPWORDS = set('a an the is are am was were be been to of for in on at and or do does did can could would should i me my we our you your please tell about what which how have has it there this that with will must would like where when who'.split())

# Maps equivalent words to one canonical token so "fee", "cost" and "price"
# all contribute to the same feature ("fees").
ALIASES = {'admission': 'admissions', 'apply': 'application', 'applying': 'application',
           'fee': 'fees', 'cost': 'fees', 'costs': 'fees', 'price': 'fees',
           'course': 'courses', 'program': 'courses', 'programs': 'courses',
           'programme': 'courses', 'programmes': 'courses', 'internship': 'internships',
           'placement': 'placements', 'scholarship': 'scholarships', 'hostels': 'hostel',
           'documents': 'document', 'required': 'require', 'requirements': 'require',
           'eligibility': 'eligible', 'companies': 'company', 'recruiters': 'company',
           'deadline': 'date', 'dates': 'date', 'employers': 'company', 'employer': 'company', 'curriculum': 'syllabus'}

# Safety thresholds used by Chatbot.predict (see the comments there).
MIN_SCORE = 0.36        # best cosine similarity must reach at least this
MIN_COVERAGE = 0.45     # share of message words that exist in the FAQ vocabulary
MIN_MARGIN = 0.07       # required lead over the second-best intent...
CONFIDENT_SCORE = 0.88  # ...unless the best score is already this high


def tokenize(text):
    """Normalize a question into comparable, lower-case tokens.

    Steps: lower-case the text, keep only letters and digits, drop stopwords,
    then replace each remaining word by its canonical alias if one exists.

    >>> tokenize("What are the tuition fees?")
    ['tuition', 'fees']
    """
    return [ALIASES.get(t, t) for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOPWORDS]


def features(text):
    """Return unigram and adjacent-bigram features for ``text``.

    Bigrams (joined with an underscore) capture short phrases such as
    ``tuition_fees`` that single words cannot express.
    """
    words = tokenize(text)
    return words + [a + '_' + b for a, b in zip(words, words[1:])]


def vectorize(text, idf):
    """Create an L2-normalized TF-IDF vector for ``text``.

    Args:
        text: the raw question.
        idf: mapping of feature -> IDF weight fitted on the training set.

    Returns:
        A sparse vector as ``{feature: weight}``. Features unseen during
        training are ignored. An empty dict is returned when nothing matches.
    """
    counts = Counter(features(text))
    # Log-scaled term frequency multiplied by the IDF weight.
    vector = {t: (1 + math.log(n)) * idf[t] for t, n in counts.items() if t in idf}
    norm = math.sqrt(sum(v * v for v in vector.values()))
    return {t: v / norm for t, v in vector.items()} if norm else {}


class Chatbot:
    """Loads the FAQ dataset, fits the TF-IDF index and answers questions."""

    def __init__(self, path=ROOT / 'data' / 'faqs.json'):
        """Fit the model from the FAQ dataset at ``path``.

        Attributes:
            data: the parsed JSON file (college name, suggestions, intents).
            intents: ``{intent_id: intent_record}`` lookup table.
            samples: list of ``(training_question, intent_id)`` pairs.
            idf: smoothed inverse document frequency per feature.
            vectors: list of ``(normalized_vector, intent_id)`` pairs.
        """
        self.data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.intents = {item['id']: item for item in self.data['intents']}
        self.samples = [(q, item['id']) for item in self.intents.values() for q in item['questions']]
        # Document frequency: in how many training questions each feature appears.
        df = Counter(t for q, _ in self.samples for t in set(features(q)))
        # Smoothed IDF: log((1 + N) / (1 + df)) + 1 avoids division by zero.
        self.idf = {t: math.log((1 + len(self.samples)) / (1 + count)) + 1 for t, count in df.items()}
        self.vectors = [(vectorize(q, self.idf), label) for q, label in self.samples]

    def predict(self, message):
        """Return a stable, JSON-serializable response for one question.

        The response always has these keys: ``answer``, ``intent``,
        ``category``, ``score`` (cosine similarity, *not* a probability),
        ``source`` and ``suggestions``.

        A fallback response (``intent == 'fallback'``) is returned when any
        of these gates fails:
          * best similarity below ``MIN_SCORE``;
          * too few words known to the FAQ vocabulary (``MIN_COVERAGE``);
          * the best intent barely beats the runner-up (``MIN_MARGIN``)
            while its score is not already very high (``CONFIDENT_SCORE``).
        """
        vector = vectorize(message, self.idf)
        # Best cosine similarity per intent (max over that intent's examples).
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
        if best < MIN_SCORE or coverage < MIN_COVERAGE or (best - second < MIN_MARGIN and best < CONFIDENT_SCORE):
            return {'answer': "I couldn't confidently match that question to the FAQ. Try asking one question about admissions, courses, fees, internships, or placements. For a confirmed answer, contact your college office.",
                    'intent': 'fallback', 'category': 'Help', 'score': round(best, 3),
                    'source': 'No reliable FAQ match', 'suggestions': self.data['suggestions'][:3]}
        intent = self.intents[best_id]
        return {'answer': intent['answer'], 'intent': best_id, 'category': intent['category'],
                'score': round(best, 3), 'source': intent['source'],
                'suggestions': intent.get('suggestions', self.data['suggestions'][:3])}

    def export(self, path):
        """Write an inspection artifact (IDF weights and vectors) to ``path``.

        The runtime never reads this file; it exists so students can inspect
        what the model learned. Regenerate it with ``python train.py``.
        """
        artifact = {'algorithm': 'TF-IDF word + bigram cosine nearest-example intent classifier',
                    'training_questions': len(self.samples), 'intent_count': len(self.intents),
                    'idf': self.idf, 'vectors': self.vectors}
        Path(path).write_text(json.dumps(artifact, indent=2), encoding='utf-8')
