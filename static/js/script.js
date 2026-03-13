
document.addEventListener('DOMContentLoaded', () => {
  loadUpcomingMatches();
  loadRecentScores();
  addBotMessage(
    "Bonjour&nbsp;! 👋 Bienvenue sur <b>FootBot</b>, votre assistant de réservation de billets de football&nbsp;!<br><br>" +
    "Je peux vous aider à&nbsp;:<br>" +
    "⚽ Voir les <b>scores récents</b><br>" +
    "📅 Consulter les <b>prochains matchs</b><br>" +
    "🎫 <b>Réserver une place</b><br>" +
    "🔮 Obtenir une <b>prédiction de match</b><br><br>" +
    "Que puis-je faire pour vous&nbsp;?"
  );
});

async function loadUpcomingMatches() {
  try {
    const res    = await fetch('/api/matchs_futurs');
    const matchs = await res.json();
    const box    = document.getElementById('upcoming-matches');
    box.innerHTML = '';

    matchs.forEach(m => {
      const card = document.createElement('div');
      card.className = 'match-card';
      const dispo = m.places_restantes > 0
        ? `<span class="match-dispo">🎫 ${m.places_restantes} places dispo</span>`
        : `<span class="match-dispo complet">❌ Complet</span>`;
      card.innerHTML =
        `<div class="match-teams">${m.domicile} vs ${m.exterieur}</div>` +
        `<div class="match-meta">📅 ${m.date} à ${m.heure}</div>` +
        `<div class="match-meta">🏟️ ${m.stade} · ${m.competition}</div>` +
        dispo;
      if (m.places_restantes > 0) {
        card.title = 'Cliquez pour réserver ce match';
        card.onclick = () => quickAction(`Réserver le match ${m.domicile} vs ${m.exterieur}`);
      }
      box.appendChild(card);
    });
  } catch (e) {
    document.getElementById('upcoming-matches').innerHTML =
      '<div class="match-meta">Erreur de chargement</div>';
  }
}

async function loadRecentScores() {
  try {
    const res    = await fetch('/api/scores_recents');
    const scores = await res.json();
    const box    = document.getElementById('recent-scores');
    box.innerHTML = '';

    scores.forEach(s => {
      const card = document.createElement('div');
      card.className = 'score-card';
      card.innerHTML =
        `<div class="score-row">` +
          `<span class="score-team">${s.domicile}</span>` +
          `<span class="score-result">${s.score}</span>` +
          `<span class="score-team right">${s.exterieur}</span>` +
        `</div>` +
        `<div class="score-comp">${s.competition} · ${s.date}</div>`;
      box.appendChild(card);
    });
  } catch (e) {
    document.getElementById('recent-scores').innerHTML =
      '<div class="score-comp">Erreur de chargement</div>';
  }
}

async function sendMessage() {
  const input   = document.getElementById('user-input');
  const message = input.value.trim();
  if (!message) return;

  addUserMessage(message);
  input.value = '';
  input.focus();

  const typing = showTyping();

  try {
    const res  = await fetch('/get_response', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message }),
    });
    const data = await res.json();
    removeTyping(typing);
    addBotMessage(data.response || 'Réponse vide.');
  } catch (err) {
    removeTyping(typing);
    addBotMessage('❌ Erreur de connexion au serveur. Veuillez réessayer.');
  }
}

function quickAction(text) {
  document.getElementById('user-input').value = text;
  sendMessage();
}

function addUserMessage(text) {
  const box     = document.getElementById('chat-box');
  const wrapper = document.createElement('div');
  wrapper.className = 'message user-msg';
  wrapper.innerHTML =
    `<div class="msg-wrapper">` +
      `<div class="msg-sender">Vous</div>` +
      `<div class="msg-bubble">${escapeHtml(text)}</div>` +
    `</div>`;
  box.appendChild(wrapper);
  scrollChat();
}

function addBotMessage(html) {
  const box     = document.getElementById('chat-box');
  const wrapper = document.createElement('div');
  wrapper.className = 'message bot-msg';
  wrapper.innerHTML =
    `<div class="bot-avatar">⚽</div>` +
    `<div class="msg-wrapper">` +
      `<div class="msg-sender">FootBot</div>` +
      `<div class="msg-bubble">${html}</div>` +
    `</div>`;
  box.appendChild(wrapper);
  scrollChat();
}

function showTyping() {
  const box     = document.getElementById('chat-box');
  const wrapper = document.createElement('div');
  wrapper.className = 'message bot-msg';
  wrapper.innerHTML =
    `<div class="bot-avatar">⚽</div>` +
    `<div class="typing-indicator">` +
      `<div class="typing-dot"></div>` +
      `<div class="typing-dot"></div>` +
      `<div class="typing-dot"></div>` +
    `</div>`;
  box.appendChild(wrapper);
  scrollChat();
  return wrapper;
}

function removeTyping(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

function scrollChat() {
  const box = document.getElementById('chat-box');
  box.scrollTop = box.scrollHeight;
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(text));
  return d.innerHTML;
}

document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.activeElement === document.getElementById('user-input')) {
    sendMessage();
  }
});
