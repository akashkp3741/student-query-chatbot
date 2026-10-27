/*
 * CampusGuide - browser client
 * Project owner: Nayana K C
 *
 * Connects the chat interface to the Python API:
 *   GET  /api/info  -> fills the college name and data notice on load.
 *   POST /api/chat  -> sends {message} and renders the {answer, category,
 *                      source, suggestions} reply.
 * If the API cannot be reached, the question is put back in the input box so
 * the student can retry without retyping.
 */

/** Shorthand for document.getElementById. */
const $ = (id) => document.getElementById(id);

/** True while a request is in flight; prevents double submissions. */
let busy = false;

/** Suggestion chips shown before the server returns its own suggestions. */
let defaults = ['Are scholarships available?', 'Can I get an internship?'];

/**
 * Render up to three clickable suggestion chips above the input box.
 * @param {string[]} items - suggested questions.
 */
function suggestions(items) {
  $('suggestions').replaceChildren();
  items.slice(0, 3).forEach((text) => {
    const button = document.createElement('button');
    button.textContent = text;
    button.type = 'button';
    button.addEventListener('click', () => send(text));
    $('suggestions').append(button);
  });
}

/**
 * Append one chat bubble to the conversation.
 * Text is inserted with textContent (never innerHTML) so replies cannot
 * inject markup into the page.
 * @param {'user'|'bot'} role - who is speaking.
 * @param {string} text - message text.
 * @param {object} [result] - API response; adds a category tag and source line.
 * @returns {HTMLElement} the created <article>, so callers can remove it.
 */
function message(role, text, result) {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  const author = document.createElement('div');
  author.className = 'author';
  author.textContent = role === 'user' ? 'YOU' : 'CAMPUSGUIDE';
  if (result?.category) {
    const tag = document.createElement('span');
    tag.className = 'category';
    tag.textContent = result.category;
    author.append(tag);
  }
  const body = document.createElement('div');
  body.className = 'body';
  body.textContent = text;
  article.append(author, body);
  if (result?.source) {
    const source = document.createElement('div');
    source.className = 'source';
    source.textContent = result.source;
    article.append(source);
  }
  $('conversation').append(article);
  return article;
}

/**
 * Send a question to POST /api/chat and show the answer.
 * Disables the controls while waiting, shows a temporary "finding" bubble,
 * and restores the input text if the request fails.
 * @param {string} text - the student's question.
 */
async function send(text) {
  if (busy || !text.trim()) return;
  busy = true;
  $('send').disabled = true;
  $('new-chat').disabled = true;
  $('welcome').hidden = true;
  $('conversation').hidden = false;
  $('question').value = '';
  $('question').style.height = '';
  message('user', text.trim());
  const pending = message('bot', 'Finding the right FAQ…');
  pending.scrollIntoView({block: 'nearest'});
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text.trim()}), signal: AbortSignal.timeout(15000)
    });
    const result = await response.json();
    // 400/413 responses carry an {error} message from the server.
    if (!response.ok) throw new Error(result.error || 'Unable to send your question.');
    pending.remove();
    message('bot', result.answer, result);
    suggestions(result.suggestions || defaults);
    $('status').textContent = 'Ready to help';
  } catch (error) {
    pending.remove();
    message('bot', 'Could not reach the chatbot. Check that the Python app is running, then try again.');
    $('question').value = text; // let the student retry without retyping
    $('status').textContent = 'Connection interrupted';
  } finally {
    busy = false;
    $('send').disabled = false;
    $('new-chat').disabled = false;
    $('question').focus({preventScroll: true});
    $('chat-form').scrollIntoView({block: 'nearest'});
  }
}

// ---------- Event wiring ----------

// Submit button / form submit.
$('chat-form').addEventListener('submit', (event) => { event.preventDefault(); send($('question').value); });

// Enter sends; Shift+Enter inserts a newline; ignore Enter while an IME is composing.
$('question').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(event.target.value); }
});

// Auto-grow the textarea up to 130px (matches max-height in style.css).
$('question').addEventListener('input', (event) => { event.target.style.height = 'auto'; event.target.style.height = Math.min(event.target.scrollHeight, 130) + 'px'; });

// Topic cards and sidebar links carry their question in data-question.
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => send(button.dataset.question)));

// "New conversation": clear messages and return to the welcome screen.
$('new-chat').addEventListener('click', () => {
  $('conversation').replaceChildren();
  $('conversation').hidden = true;
  $('welcome').hidden = false;
  $('question').value = '';
  suggestions(defaults);
  window.scrollTo({top: 0});
});

// ---------- Start-up ----------
suggestions(defaults);

// GET /api/info: show the configured college name and data notice.
fetch('/api/info').then((response) => { if (!response.ok) throw new Error('Unavailable'); return response.json(); }).then((info) => {
  $('college').textContent = info.college;
  $('status').textContent = 'Ready to help';
  if (!info.sample_data) {
    $('data-note').textContent = 'Answers from the configured college FAQ. Confirm current details with your college.';
    $('footer-note').textContent = 'College FAQ answers · confirm current details';
  }
}).catch(() => { $('status').textContent = 'Connection unavailable'; });
