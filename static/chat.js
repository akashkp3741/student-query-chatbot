const $ = (id) => document.getElementById(id);
let busy = false;
let defaults = ['Are scholarships available?', 'Can I get an internship?'];

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
    if (!response.ok) throw new Error(result.error || 'Unable to send your question.');
    pending.remove();
    message('bot', result.answer, result);
    suggestions(result.suggestions || defaults);
    $('status').textContent = 'Ready to help';
  } catch (error) {
    pending.remove();
    message('bot', 'Could not reach the chatbot. Check that the Python app is running, then try again.');
    $('question').value = text;
    $('status').textContent = 'Connection interrupted';
  } finally {
    busy = false;
    $('send').disabled = false;
    $('new-chat').disabled = false;
    $('question').focus({preventScroll: true});
    $('chat-form').scrollIntoView({block: 'nearest'});
  }
}

$('chat-form').addEventListener('submit', (event) => { event.preventDefault(); send($('question').value); });
$('question').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(event.target.value); }
});
$('question').addEventListener('input', (event) => { event.target.style.height = 'auto'; event.target.style.height = Math.min(event.target.scrollHeight, 130) + 'px'; });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => send(button.dataset.question)));
$('new-chat').addEventListener('click', () => {
  $('conversation').replaceChildren();
  $('conversation').hidden = true;
  $('welcome').hidden = false;
  $('question').value = '';
  suggestions(defaults);
  window.scrollTo({top: 0});
});
suggestions(defaults);
fetch('/api/info').then((response) => { if (!response.ok) throw new Error('Unavailable'); return response.json(); }).then((info) => {
  $('college').textContent = info.college;
  $('status').textContent = 'Ready to help';
  if (!info.sample_data) {
    $('data-note').textContent = 'Answers from the configured college FAQ. Confirm current details with your college.';
    $('footer-note').textContent = 'College FAQ answers · confirm current details';
  }
}).catch(() => { $('status').textContent = 'Connection unavailable'; });
