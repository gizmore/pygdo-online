window.gdo = window.gdo || {};
window.gdo.online = {
    openUsers: function(url) {
        const popup = document.getElementById('online-user-popup') || document.body.appendChild(document.createElement('dialog'));
        popup.id = 'online-user-popup';
        popup.className = 'online-user-popup';
        popup.innerHTML = '<button class="online-user-popup-close" aria-label="Close">×</button><div class="online-user-grid">Loading…</div>';
        popup.querySelector('.online-user-popup-close').onclick = () => popup.close();
        popup.showModal();
        fetch(url).then((response) => response.json()).then((payload) => {
            const users = payload.data || [];
            popup.querySelector('.online-user-grid').innerHTML = users.map((user) =>
                `<a class="gdt-link" href="${user.profile}">${user.avatar ? `<span class="gdo-avatar"><img src="${user.avatar}" alt=""></span> ` : ''}${user.name}</a>`
            ).join('') || 'Nobody is online.';
        });
        return false;
    },
    refreshCount: async function() {
        const link = document.querySelector('[data-online-counter]');
        if (!link) return;
        try {
            const response = await fetch(link.dataset.onlineCountUrl, {cache: 'no-store'});
            if (!response.ok) return;
            const payload = await response.json();
            if (!payload.data || !Number.isInteger(payload.data.users)) return;
            const previous = link.dataset.onlineCounter;
            const previousGuests = link.dataset.onlineGuests;
            const previousViewers = link.dataset.onlineViewers;
            const guests = payload.data.guests === null ? '?' : String(payload.data.guests);
            const viewers = Number.isInteger(payload.data.stream_viewers) ? String(payload.data.stream_viewers) : '?';
            const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const counts = new RegExp('(' + escape(previous) + ')(\\s*\\(\\+)' + escape(previousGuests) + '(\\))');
            const walker = document.createTreeWalker(link, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (counts.test(node.nodeValue)) {
                    node.nodeValue = node.nodeValue.replace(counts, (_, first, between, close) => String(payload.data.users) + between + guests + close);
                    node.nodeValue = node.nodeValue.replace(new RegExp('(·\\s*)' + escape(previousViewers) + '(\\s+watching)'), (_, prefix, suffix) => prefix + viewers + suffix);
                    link.dataset.onlineCounter = String(payload.data.users);
                    link.dataset.onlineGuests = guests;
                    link.dataset.onlineViewers = viewers;
                    break;
                }
            }
        } catch (_) {
            // Keep the last known count on temporary network failures.
        }
    },
};
document.addEventListener('DOMContentLoaded', () => {
    const link = document.querySelector('[data-online-counter]');
    if (link) {
        const interval = Number(link.dataset.onlineRefreshMs);
        if (Number.isFinite(interval) && interval >= 1000) {
            window.setInterval(() => window.gdo.online.refreshCount(), interval);
        }
    }
});
