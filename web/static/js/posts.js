document.addEventListener('DOMContentLoaded', () => {
    loadPosts();
});

async function loadPosts() {
    const grid = document.getElementById('posts-grid');
    grid.innerHTML = '<div class="text-muted">Loading...</div>';

    try {
        const response = await fetch('/api/posts/published');
        const data = await response.json();
        
        if (!data.posts || data.posts.length === 0) {
            grid.innerHTML = '<div class="text-muted" style="grid-column: 1/-1;">No published posts found.</div>';
            return;
        }

        grid.innerHTML = data.posts.map(post => `
            <div class="card" style="padding: 0; overflow: hidden; margin: 0;">
                <div style="padding: 1rem; border-bottom: 1px solid var(--border);">
                    <div class="flex justify-between items-center">
                        <span class="badge ${post.media_type === 'IMAGE' || post.media_type === 'CAROUSEL_ALBUM' ? 'badge-info' : 'badge-error'}">${post.media_type}</span>
                        <span class="text-sm text-muted">${post.timestamp ? new Date(post.timestamp).toLocaleDateString() : 'Unknown'}</span>
                    </div>
                </div>
                <div style="padding: 1rem;">
                    <p class="text-sm mb-4" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">${post.caption || 'No caption'}</p>
                    <a href="${post.permalink}" target="_blank" class="text-sm" style="color: var(--primary); text-decoration: none;">
                        View on Instagram ↗
                    </a>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load posts:', error);
        grid.innerHTML = '<div class="text-error" style="grid-column: 1/-1;">Failed to load posts. Check logs for details.</div>';
    }
}
