const input = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const button = document.getElementById('scanButton');
const status = document.getElementById('status');
const summary = document.getElementById('summary');
const results = document.getElementById('results');

input.addEventListener('change', () => {
  fileName.textContent = input.files.length ? input.files[0].name : 'No file selected';
});

button.addEventListener('click', async () => {
  if (!input.files.length) {
    showStatus('Please select a file first.', true);
    return;
  }

  const form = new FormData();
  form.append('file', input.files[0]);
  button.disabled = true;
  button.textContent = 'Scanning...';
  showStatus('Scanning file. Images are being processed with OCR...', false);
  summary.classList.add('hidden');
  results.innerHTML = '';

  try {
    const response = await fetch("https://pii-detector-backend.onrender.com/api/scan", { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.error || 'Scan failed');
    renderResults(data);
    showStatus(`Scan complete: ${data.finding_count} finding(s).`, false);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = 'Scan file';
  }
});

function showStatus(message, error) {
  status.textContent = message;
  status.classList.remove('hidden', 'error');
  if (error) status.classList.add('error');
}

function renderResults(data) {
  const findings = data.findings || [];
  const counts = {
    accidental: findings.filter(f => f.classification === 'LIKELY_ACCIDENTAL').length,
    intended: findings.filter(f => f.classification === 'INTENDED_DISCLOSURE').length,
    review: findings.filter(f => f.classification === 'CONTEXT_REVIEW').length
  };
  document.getElementById('total').textContent = findings.length;
  document.getElementById('accidental').textContent = counts.accidental;
  document.getElementById('intended').textContent = counts.intended;
  document.getElementById('review').textContent = counts.review;
  summary.classList.remove('hidden');

  if (!findings.length) {
    results.innerHTML = '<div class="card finding">No supported privacy findings were detected.</div>';
    return;
  }

  for (const finding of findings) {
    const card = document.createElement('article');
    card.className = 'finding';
    const badgeClass = finding.classification === 'LIKELY_ACCIDENTAL' ? 'accidental' :
      finding.classification === 'INTENDED_DISCLOSURE' ? 'intended' : 'review';
    const evidence = (finding.evidence || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
    card.innerHTML = `
      <div class="finding-head">
        <span class="kind">${escapeHtml(finding.kind)}</span>
        <span class="badge ${badgeClass}">${escapeHtml(finding.classification)}</span>
      </div>
      <div class="meta">${escapeHtml(finding.source)} · Confidence ${(finding.confidence * 100).toFixed(0)}% · Context score ${finding.context_score}</div>
      <strong>Masked value: ${escapeHtml(finding.value_masked)}</strong>
      <ul class="evidence">${evidence}</ul>
    `;
    results.appendChild(card);
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}
