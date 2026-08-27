"use strict";

window.gdo = window.gdo || {};
window.gdo.onlineUsersMap = {
    gdo_init: function() {
        const element = document.getElementById('online-map');
        if (!element || !window.L) {
            return;
        }
        // gdo_init may run again after an XHR update. Leaflet may bind a DOM
        // container only once; a replaced container has no _leaflet_id.
        if (element._leaflet_id) {
            return;
        }

        let users = [];
        try {
            users = JSON.parse(element.dataset.users || '[]');
        } catch (_) {
            return;
        }

        const map = L.map(element).setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        const bounds = [];
        users.forEach((user) => {
            const point = [user.lat, user.lng];
            bounds.push(point);
            const profile = document.createElement('span');
            if (user.avatar) {
                const avatar = document.createElement('img');
                avatar.src = user.avatar;
                avatar.alt = '';
                avatar.className = 'online-map-avatar';
                profile.append(avatar);
            }
            const profileLink = document.createElement('a');
            profileLink.href = user.profile_url;
            profileLink.textContent = user.name;
            profile.append(profileLink);
            L.marker(point)
                .addTo(map)
                .bindPopup(profile);
        });

        if (bounds.length) {
            map.fitBounds(bounds, {padding: [32, 32], maxZoom: 14});
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    window.gdo.onlineUsersMap.gdo_init();
});
