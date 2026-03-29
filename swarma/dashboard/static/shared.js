/* ============================================
   swarma -- shared JS utilities
   ============================================ */

const API = window.location.origin;

// ---- API helpers ----

async function api(path) {
  const resp = await fetch(API + path);
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

async function apiPost(path, body) {
  const resp = await fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

async function apiPut(path, body) {
  const resp = await fetch(API + path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

// ---- Sidebar ----

function renderSidebar(activePage) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  sidebar.innerHTML = `
    <div class="sidebar-brand">
      <img src="/static/icon.png" alt="">
      <h1>SWARMA</h1>
    </div>

    <a class="sidebar-cta" href="#" onclick="openNewExperiment(); return false;">+ new experiment</a>

    <div class="sidebar-section">
      <a class="sidebar-item ${activePage === 'dashboard' ? 'active' : ''}" href="/dashboard">
        <span class="icon">+</span> dashboard
      </a>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-section-title">experiments</div>
      <a class="sidebar-item ${activePage === 'experiments' ? 'active' : ''}" href="/experiments-view">
        <span class="icon">~</span> running & results
      </a>
      <a class="sidebar-item ${activePage === 'playbook' ? 'active' : ''}" href="/playbook-view">
        <span class="icon">*</span> playbook
      </a>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-section-title">swarm</div>
      <a class="sidebar-item ${activePage === 'agents' ? 'active' : ''}" href="/agents-view">
        <span class="icon">&gt;</span> agents
      </a>
      <a class="sidebar-item ${activePage === 'flow' ? 'active' : ''}" href="/flow-view">
        <span class="icon">-</span> flow
      </a>
      <a class="sidebar-item ${activePage === 'knowledge' ? 'active' : ''}" href="/knowledge-view">
        <span class="icon">#</span> knowledge
      </a>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-section-title">settings</div>
      <a class="sidebar-item ${activePage === 'settings' ? 'active' : ''}" href="/settings-view">
        <span class="icon">@</span> config
      </a>
    </div>

    <div class="sidebar-footer">
      <span class="status-dot idle" id="sidebar-status-dot"></span>
      <span id="sidebar-status-text">connecting...</span>
    </div>
  `;

  // Check health
  checkHealth();
}

async function checkHealth() {
  try {
    await api('/health');
    const dot = document.getElementById('sidebar-status-dot');
    const txt = document.getElementById('sidebar-status-text');
    if (dot) dot.className = 'status-dot ok';
    if (txt) txt.textContent = 'connected';
  } catch (e) {
    const dot = document.getElementById('sidebar-status-dot');
    const txt = document.getElementById('sidebar-status-text');
    if (dot) dot.className = 'status-dot err';
    if (txt) txt.textContent = 'disconnected';
  }
}

// ---- Modal ----

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// ---- New Experiment modal ----

function openNewExperiment() {
  openModal('new-experiment-modal');
}

async function submitNewExperiment() {
  const hypothesis = document.getElementById('exp-hypothesis')?.value?.trim();
  const metric = document.getElementById('exp-metric')?.value?.trim() || 'engagement_rate';
  const sampleSize = parseInt(document.getElementById('exp-sample-size')?.value || '5');
  const teamId = document.getElementById('exp-team')?.value?.trim() || 'default';
  const agentId = document.getElementById('exp-agent')?.value?.trim() || 'growth-lead';

  if (!hypothesis) return;

  try {
    const result = await apiPost('/experiments', {
      team_id: teamId,
      agent_id: agentId,
      hypothesis: hypothesis,
      metric_name: metric,
      sample_size: sampleSize,
    });
    closeModal('new-experiment-modal');
    showToast('experiment created');
    if (typeof onExperimentCreated === 'function') onExperimentCreated(result);
    else window.location.reload();
  } catch (e) {
    showToast('error: ' + e.message);
  }
}

// ---- Toast notifications ----

function showToast(message, duration) {
  duration = duration || 3000;
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:300;';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.style.cssText = `
    background:var(--surface-raised);border:2px solid var(--gold-dim);
    color:var(--text);padding:8px 16px;font-size:11px;margin-top:8px;
    font-family:inherit;box-shadow:2px 2px 0 var(--shadow);
  `;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// ---- Formatting helpers ----

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatCost(cost) {
  return '$' + (cost || 0).toFixed(4);
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

function formatTimestamp(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function verdictTag(verdict) {
  const cls = {
    keep: 'tag-keep',
    discard: 'tag-discard',
    running: 'tag-running',
    inconclusive: 'tag-inconclusive',
    completed: 'tag-ok',
    error: 'tag-err',
    started: 'tag-pending',
  }[verdict] || 'tag-pending';
  return `<span class="tag ${cls}">${verdict}</span>`;
}

// ---- Render New Experiment modal (shared across pages) ----

function renderNewExperimentModal() {
  if (document.getElementById('new-experiment-modal')) return;

  const modal = document.createElement('div');
  modal.id = 'new-experiment-modal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3>+ new experiment</h3>
        <button class="modal-close" onclick="closeModal('new-experiment-modal')">x</button>
      </div>
      <div class="modal-body">
        <label>hypothesis</label>
        <textarea id="exp-hypothesis" placeholder="failure stories generate more comments than success stories" style="min-height:60px"></textarea>
        <div class="hint">what are you testing? one variable, one change.</div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px">
          <div>
            <label style="margin-top:0">metric</label>
            <select id="exp-metric">
              <option value="engagement_rate">engagement rate</option>
              <option value="comment_rate">comment rate</option>
              <option value="save_rate">save rate</option>
              <option value="impressions">impressions</option>
              <option value="click_rate">click rate</option>
              <option value="custom">custom</option>
            </select>
          </div>
          <div>
            <label style="margin-top:0">sample size</label>
            <input id="exp-sample-size" type="number" value="5" min="1" max="100">
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px">
          <div>
            <label style="margin-top:0">team</label>
            <input id="exp-team" value="default" placeholder="default">
          </div>
          <div>
            <label style="margin-top:0">agent</label>
            <input id="exp-agent" value="growth-lead" placeholder="growth-lead">
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn" onclick="closeModal('new-experiment-modal')">cancel</button>
        <button class="btn btn-gold" onclick="submitNewExperiment()">run experiment</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

// ---- Init (call on every page) ----

document.addEventListener('DOMContentLoaded', () => {
  renderNewExperimentModal();
});
