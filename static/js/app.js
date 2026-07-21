/* ============================================================
   Future Envelope — client-side behavior
   Private/recipient toggle, char counter, delivery presets,
   photobooth-style photo strip picker, generic file chips,
   and live countdowns.
   ============================================================ */

// ── Compose / Edit page ─────────────────────────────────────
function initComposePage(opts = {}) {
  const maxPhotos = opts.maxPhotos || 6;
  const maxAttachments = opts.maxAttachments || 8;

  const isPrivate = document.getElementById('is_private');
  const recipientGroup = document.getElementById('recipient-group');
  function syncPrivate() {
    if (!isPrivate || !recipientGroup) return;
    recipientGroup.style.display = isPrivate.checked ? 'none' : '';
  }
  if (isPrivate) {
    isPrivate.addEventListener('change', syncPrivate);
    syncPrivate();
  }

  const body = document.getElementById('body');
  const charCount = document.getElementById('char-count');
  if (body && charCount) {
    const updateCount = () => { charCount.textContent = body.value.length; };
    body.addEventListener('input', updateCount);
    updateCount();
  }

  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const offsetSeconds = parseInt(btn.dataset.offset, 10);
      const target = new Date(Date.now() + offsetSeconds * 1000);
      const scheduledInput = document.getElementById('scheduled_at');
      if (scheduledInput) scheduledInput.value = toLocalInputValue(target);
    });
  });

  initPhotoStrip(maxPhotos);
  initFilePreview(maxAttachments);
}

function toLocalInputValue(date) {
  const pad = n => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// ── Photo strip picker ───────────────────────────────────────
function initPhotoStrip(maxPhotos) {
  const input = document.getElementById('photo-input');
  const addBtn = document.getElementById('add-photo-btn');
  const strip = document.getElementById('photo-strip');
  if (!input || !strip) return;

  const files = [];

  if (addBtn) addBtn.addEventListener('click', () => input.click());

  input.addEventListener('change', () => {
    for (const f of input.files) {
      if (!f.type.startsWith('image/')) continue;
      if (files.length >= maxPhotos) {
        alert(`You can only add up to ${maxPhotos} photos to the strip.`);
        break;
      }
      files.push(f);
    }
    syncInputFiles();
    renderStrip();
  });

  function syncInputFiles() {
    const dt = new DataTransfer();
    files.forEach(f => dt.items.add(f));
    input.files = dt.files;
  }

  function renderStrip() {
    strip.innerHTML = '';
    files.forEach((file, idx) => {
      const frame = document.createElement('div');
      frame.className = 'photo-frame';

      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.alt = file.name;

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'photo-frame-remove';
      removeBtn.title = 'Remove photo';
      removeBtn.textContent = '✕';
      removeBtn.addEventListener('click', () => {
        files.splice(idx, 1);
        syncInputFiles();
        renderStrip();
      });

      frame.appendChild(img);
      frame.appendChild(removeBtn);
      strip.appendChild(frame);
    });
  }
}

// ── Generic "other files" preview ───────────────────────────
function initFilePreview(maxAttachments) {
  const input = document.getElementById('attachments');
  const preview = document.getElementById('file-preview');
  if (!input || !preview) return;

  const files = [];

  input.addEventListener('change', () => {
    for (const f of input.files) {
      if (files.length >= maxAttachments) {
        alert(`You can only attach up to ${maxAttachments} files.`);
        break;
      }
      files.push(f);
    }
    syncInputFiles();
    renderPreview();
  });

  function syncInputFiles() {
    const dt = new DataTransfer();
    files.forEach(f => dt.items.add(f));
    input.files = dt.files;
  }

  function renderPreview() {
    preview.innerHTML = '';
    files.forEach((file, idx) => {
      const chip = document.createElement('div');
      chip.className = 'file-chip';

      const name = document.createElement('span');
      name.className = 'file-chip-name';
      name.textContent = file.name;

      const size = document.createElement('span');
      size.className = 'file-chip-size';
      size.textContent = formatBytes(file.size);

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'file-chip-remove';
      removeBtn.title = 'Remove file';
      removeBtn.textContent = '✕';
      removeBtn.addEventListener('click', () => {
        files.splice(idx, 1);
        syncInputFiles();
        renderPreview();
      });

      chip.appendChild(name);
      chip.appendChild(size);
      chip.appendChild(removeBtn);
      preview.appendChild(chip);
    });
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let n = bytes / 1024, i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(1)} ${units[i]}`;
}

// ── Countdowns ───────────────────────────────────────────────
function formatCountdown(seconds) {
  if (seconds <= 0) return 'Any moment now…';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const parts = [];
  if (d) parts.push(`${d}d`);
  if (d || h) parts.push(`${h}h`);
  if (d || h || m) parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(' ');
}

function updateCountdown(el) {
  // scheduled_at is stored/rendered as a naive UTC isoformat string — force UTC parsing.
  const target = new Date(el.dataset.target + 'Z');
  const seconds = (target.getTime() - Date.now()) / 1000;
  el.textContent = formatCountdown(seconds);
}

function initCountdowns() {
  document.querySelectorAll('.countdown').forEach(el => {
    updateCountdown(el);
    setInterval(() => updateCountdown(el), 1000);
  });
}

function refreshCountdowns() {
  fetch('/api/emails')
    .then(r => r.json())
    .then(data => {
      const liveIds = new Set(data.map(e => String(e.id)));
      let changed = false;
      document.querySelectorAll('.envelope-card').forEach(card => {
        if (!liveIds.has(card.dataset.id)) changed = true;
      });
      if (changed) window.location.reload();
    })
    .catch(() => {});
}
