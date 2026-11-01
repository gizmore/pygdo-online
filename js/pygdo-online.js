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
            const response = await fetch(link.href, {cache: 'no-store'});
            if (!response.ok) return;
            const payload = await response.json();
            if (!Array.isArray(payload.data)) return;
            const previous = link.dataset.onlineCounter;
            const walker = document.createTreeWalker(link, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.nodeValue.includes(previous)) {
                    node.nodeValue = node.nodeValue.replace(previous, String(payload.data.length));
                    link.dataset.onlineCounter = String(payload.data.length);
                    break;
                }
            }
        } catch (_) {
            // Keep the last known count on temporary network failures.
        }
    },
};
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('[data-online-counter]')) {
        window.setInterval(() => window.gdo.online.refreshCount(), 60000);
    }
});
