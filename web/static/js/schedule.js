document.addEventListener('DOMContentLoaded', () => {
    loadScheduled();
});

async function loadScheduled() {
    const container = document.getElementById('schedule-container');
    container.innerHTML = '<div class="text-muted">Loading scheduled queue...</div>';

    const statusFilter = document.getElementById('schedule-status-filter');
    const status = statusFilter ? statusFilter.value : '';
    const url = status ? `/api/posts/scheduled?status_filter=${encodeURIComponent(status)}` : '/api/posts/scheduled';

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }
        const data = await response.json();

        if (!data.posts || data.posts.length === 0) {
            container.innerHTML = '<div class="text-muted">No scheduled or failed posts. Use Posting → Schedule (Optional) or Batch to add some.</div>';
            return;
        }

        container.innerHTML = `
            <div class="card" style="overflow-x: auto;">
                <table class="log-table" style="width: 100%;">
                    <thead>
                        <tr>
                            <th>When</th>
                            <th>Account</th>
                            <th>Type</th>
                            <th>Preview</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.posts.map(p => row(p)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load scheduled posts:', error);
        container.innerHTML = `<div class="text-error">Failed to load scheduled queue: ${error.message}</div>`;
    }
}

function row(p) {
    const st = (p.scheduled_time || '').replace('Z', '').split('+')[0];
    const when = st ? (() => { try { return new Date(st).toLocaleString(); } catch (_) { return st; } })() : '—';
    const account = (p.account_id || '—').slice(0, 12) + (p.account_id && p.account_id.length > 12 ? '…' : '');
    const mediaType = p.media_type || '—';
    const url0 = (p.urls && p.urls[0]) ? p.urls[0] : '';
    const url0Esc = url0 ? url0.replace(/"/g, '&quot;').replace(/</g, '&lt;') : '';
    const preview = url0 ? `<a href="${url0Esc}" target="_blank" rel="noopener" class="text-sm">${url0.slice(0, 40).replace(/</g, '&lt;')}…</a>` : '—';
    const status = (p.status || 'scheduled').toLowerCase();
    const statusBadge = status === 'failed'
        ? '<span class="badge badge-error">Failed</span>'
        : '<span class="badge badge-info">Scheduled</span>';
    const err = (p.error_message || '').slice(0, 80) + (p.error_message && p.error_message.length > 80 ? '…' : '');
    const errCell = status === 'failed' && err
        ? `<div class="text-sm text-error" title="${(p.error_message || '').replace(/"/g, '&quot;')}">${err.replace(/</g, '&lt;')}</div>`
        : '';

    let actions = '';
    if (status === 'failed') {
        actions += `<button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" onclick="retryScheduled('${p.id}')">Retry</button> `;
    }
    actions += `<button class="btn btn-danger" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" onclick="cancelScheduled('${p.id}')">Cancel</button>`;

    return `
        <tr class="log-row">
            <td>${when}</td>
            <td><code class="text-sm">${account}</code></td>
            <td>${mediaType}</td>
            <td>${preview}</td>
            <td>${statusBadge}${errCell}</td>
            <td>${actions}</td>
        </tr>
    `;
}

async function retryScheduled(id) {
    try {
        const r = await fetch(`/api/posts/scheduled/${id}/retry`, { method: 'PATCH' });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
        alert('Post requeued. It will be published when due.');
        loadScheduled();
    } catch (e) {
        alert('Retry failed: ' + e.message);
    }
}

async function cancelScheduled(id) {
    if (!confirm('Remove this post from the schedule?')) return;
    try {
        const r = await fetch(`/api/posts/scheduled/${id}`, { method: 'DELETE' });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
        loadScheduled();
    } catch (e) {
        alert('Cancel failed: ' + e.message);
    }
}
