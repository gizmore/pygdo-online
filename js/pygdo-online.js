window.gdo = window.gdo || {};
window.gdo.online = {
    openUsers: function(url) {
        debugger;
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
};
