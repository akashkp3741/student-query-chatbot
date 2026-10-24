# AI Chatbot for Student Queries

## Abstract

CampusGuide is a browser-based FAQ chatbot designed to help students find information about admissions, courses, fees, internships, and placements. It normalizes questions, represents training examples with TF-IDF features, identifies the closest intent through cosine similarity, and retrieves a curated response. A fallback handles questions that do not match confidently. The submitted implementation uses an explicitly labeled sample dataset and runs entirely on a local computer.

## Problem and objective

Students frequently ask similar questions, while staff may be unavailable outside office hours. The objective is to demonstrate an accessible conversational interface that automatically retrieves consistent answers from a maintained knowledge base. Official facts must be supplied before the system can serve as a real college information service.

## Architecture

Student question → browser interface → POST /api/chat → preprocessing → TF-IDF vector → cosine comparison with training examples → intent selection or fallback → curated answer → browser.

## Modules

1. **Dataset:** JSON records containing intent identifiers, question examples, response text, topic, source label, and optional follow-up suggestions.
2. **Preprocessing:** lowercasing, tokenization, stopword removal, and normalization of common equivalent words.
3. **Feature extraction:** word and adjacent-word-pair features; log-scaled term frequency and smoothed inverse document frequency; L2 normalization.
4. **Intent classification:** each training question has a vector and label. The maximum cosine similarity per intent determines the closest match. Score, score margin, and vocabulary coverage gate the result.
5. **Response mapping:** return the matching intent's answer; do not generate unsupported college facts.
6. **Interface and API:** browser chat with suggested questions and a Python HTTP API.

## Algorithm

For term t, IDF(t) = log((1 + N) / (1 + df(t))) + 1. A feature's weight is (1 + log(tf)) × IDF. Normalize each vector to unit length, then calculate cosine similarity as its dot product with a training vector. Select the intent with the highest scoring example. The score is not a probability.

The classifier is a non-parametric nearest-example NLP model. Training fits the feature vocabulary and IDF weights and builds the labeled vector index. It does not involve neural-network weight optimization or an external AI API.

## Demonstration sequence

1. Launch the app and point out the sample-data notice.
2. Ask “How do I apply for admission?” and show the mapped answer and follow-up suggestions.
3. Ask “What are the tuition fees?” and explain why the demo avoids unverified amounts.
4. Ask about internships and placements to demonstrate different intents.
5. Ask “What is the weather tomorrow?” to demonstrate the fallback.
6. Start a new conversation.
7. Show the editable JSON dataset, training export, and automated checks.

## Evaluation

The included regression suite covers representative paraphrases, unsupported questions, dataset validity, API handling, and static file boundaries. It is used during development; it is not an independent benchmark. A future academic evaluation should use independently collected, labeled student questions. Report intent accuracy, precision and recall per class, fallback behavior, response latency, dataset size, and limitations. Do not report invented accuracy or placement/admission facts.

## Mapping to the supplied PDF

- Scope: the five specified student-query domains are included.
- Dataset: local editable JSON; presently illustrative rather than collected from a college.
- Cleaning and vectorization: normalization, stopword removal, TF-IDF features.
- NLP and training: labeled nearest-example intent classification.
- Response mapping: maintained answer per intent.
- Interface and integration: web chat connected to the Python backend API.
- Testing and deployment: regression tests and a working local deployment. Production hosting is not included.

## Limitations and extensions

Single-turn English questions work best. Lexical similarity can miss paraphrases and can misunderstand negation or questions with several intents. The app has no authentication, student records, application submission, or live college-system integration. Future work could add a verified college dataset, multilingual support, sentence embeddings, a protected content editor, an independent evaluation set, and production hosting.

## Viva questions

**Why TF-IDF?** It is lightweight, interpretable, and suitable for a small domain-specific FAQ dataset.

**How is the intent detected?** The question vector is compared with labeled examples and the best supported intent is selected.

**Why not hard-coded keyword rules?** Multiple weighted word and phrase features contribute to a match, allowing some variations in phrasing.

**Does it learn from chats?** No. Update the curated dataset and restart to retrain. Chat messages are not saved.

**What happens to unknown questions?** Low similarity, low known-vocabulary coverage, or close competing scores trigger a fallback. This is imperfect and requires evaluation.

**Is this a large language model?** No. It is a classical NLP retrieval and intent-classification system that chooses a curated answer.
