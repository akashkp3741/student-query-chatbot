# CampusGuide — Student Query Chatbot

**Project owner:** Nayana K C

CampusGuide is a small, explainable student-support chatbot. It combines a responsive browser interface with a Python standard-library HTTP API and a deterministic TF-IDF nearest-example classifier. The project is designed for a classroom demo or minor project: answers come from an editable FAQ dataset and the fallback avoids inventing official college facts.

## Features

- Responsive desktop, tablet, and mobile chat interface.
- Accessible topic cards, keyboard submit, loading state, error recovery, reduced-motion support, and new-conversation control.
- SVG brand mark and favicon with no external image dependency.
- Admissions, courses, fees, scholarships, internships, placements, hostel, greeting, and fallback intents.
- Word normalization, aliases, unigram and bigram TF-IDF vectors, cosine similarity, confidence threshold, and vocabulary coverage gate.
- No third-party packages, API keys, database, telemetry, or saved chat history.
- Fully documented source modules, API contract, project structure, testing, and deployment limitations.

## Quick start

Requires Python 3.10 or newer.

### Windows

Double-click `start.bat`, then open <http://127.0.0.1:8000>.

### Any supported terminal

```text
python app.py
```

If port 8000 is busy:

```text
python app.py --port 8001
```

The server binds to localhost only. Stop it with `Ctrl+C`.

## API contract

The frontend calls these endpoints directly:

### `GET /api/info`

Returns the configured college name, whether the dataset is sample data, suggested questions, and dataset counts.

### `POST /api/chat`

Request body:

```json
{"message":"How do I apply for admission?"}
```

Successful response:

```json
{
  "answer": "...",
  "intent": "admission_process",
  "category": "Admissions",
  "score": 0.842,
  "source": "Sample FAQ",
  "suggestions": ["..."]
}
```

Messages must contain 1–500 characters. Requests larger than 8192 bytes return `413`; malformed or invalid payloads return `400`; unknown paths return `404`. The browser keeps the API calls in `static/chat.js`, so replacing the backend with a compatible service only requires updating that client module.

## Data and model

Edit `data/faqs.json` to customize the assistant:

1. Set `college` to the institution name.
2. Replace sample answers with approved information.
3. Add the official source URL or document title and verification date to each `source` field.
4. Add realistic question examples to each intent.
5. Set `sample_data` to `false` only after the content has been verified.

At startup, `model.py` loads the dataset, tokenizes each question, normalizes common aliases, creates word and adjacent-word-pair features, calculates smoothed inverse document frequency, and stores normalized example vectors. A user message is compared with each labeled example. The best match is rejected when similarity, known-vocabulary coverage, or the margin over the next-best intent is too low.

This is not a generative AI model and its `score` is cosine similarity, not a calibrated probability. It is intentionally transparent and safe for a small FAQ dataset.

## Training export and tests

Export an inspection artifact:

```text
python train.py
```

Run all regression tests:

```text
python -m unittest discover -s tests -v
```

The tests cover representative paraphrases, fallback behavior, dataset integrity, API validation, static assets, and protection against arbitrary file access.

## Project structure

```text
app.py                 Standard-library HTTP server and API validation
model.py               Tokenization, TF-IDF fitting, classification, response mapping
train.py               Optional model export command
model.json             Generated model artifact for inspection
data/faqs.json         Editable intents, answers, sources, and suggestions
static/index.html      Semantic, responsive application shell
static/style.css       Design system and responsive layout
static/chat.js         Browser state, API calls, rendering, and recovery
static/logo.svg        Local SVG logo and favicon
PROJECT_NOTES.md       Architecture, demonstration, evaluation, and viva notes
tests/test_chatbot.py  Automated regression suite
start.bat              Windows launcher
```

## Security and deployment notes

This demo intentionally serves only allow-listed static files, limits request size, sets no-store and basic security headers, and does not log question text. It is not a production deployment. A public release would need HTTPS, a production WSGI/ASGI server, rate limiting, structured monitoring, authenticated content administration, secure secrets handling, and a maintained official knowledge base. Never add passwords, private student records, or confidential documents to `data/faqs.json`.

## Project owner

This project is owned and maintained by **Nayana K C**. The GitHub repository, local Git identity, and PowerShell commands below should all use the same name.

Set the Git identity once in PowerShell (use the e-mail address of the GitHub account):

```powershell
git config --global user.name "Nayana K C"
git config --global user.email "your-github-email@example.com"
```

## License

No license is asserted by this demo project. Add the license required by your course, institution, or deployment context before publishing publicly.