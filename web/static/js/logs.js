document.addEventListener('DOMContentLoaded', () => {
    loadLogs();
    // Auto-refresh every 10 seconds
    setInterval(loadLogs, 10000);
});

async function loadLogs() {
    const tbody = document.getElementById('logs-body');
    const level = document.getElementById('log-level').value;
    
    // Don't clear content if auto-refreshing, just update
    // But if manual refresh (via button calling this), we might want to show loading state? 
    // For now, let's just replace content silently.
    
    try {
        const url = level ? `/api/logs?level=${level}` : '/api/logs';
        const response = await fetch(url);
        const data = await response.json();
        
        if (!data.logs || data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-muted" style="padding: 1rem;">No logs found.</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => {
            let badgeStyle = '';
            if (log.level === 'WARNING') badgeStyle = 'background: #FEF3C7; color: #92400E;';
            if (log.level === 'ERROR') badgeStyle = 'background: #FEE2E2; color: #991B1B;';
            if (log.level === 'INFO') badgeStyle = 'background: #DBEAFE; color: #1E40AF;';
            
            let message = log.message;
            if (log.data && Object.keys(log.data).length > 0) {
                // Pretty print specific fields if needed, or just JSON
                message += `<br><span class="text-muted text-sm" style="font-size: 0.8rem;">${JSON.stringify(log.data)}</span>`;
            }

            return `
            <tr class="log-row">
                <td class="text-sm font-mono" style="white-space: nowrap;">${new Date(log.timestamp).toLocaleTimeString()}</td>
                <td><span class="badge" style="${badgeStyle}">${log.level}</span></td>
                <td class="font-mono text-sm" style="word-break: break-all;">${message}</td>
            </tr>
        `}).join('');

    } catch (error) {
        console.error('Failed to load logs:', error);
        // Only show error if table is empty
        if (tbody.children.length <= 1) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-error" style="padding: 1rem;">Failed to load logs.</td></tr>';
        }
    }
}
