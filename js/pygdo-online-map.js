"use strict";

window.gdo = window.gdo || {};
window.gdo.onlineUsersMap = {
    gdo_init: function() {
        const element = document.getElementById('online-map');
        if (!element || !window.L) {
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
            L.marker(point).addTo(map).bindTooltip(user.name);
        });

        if (bounds.length) {
            map.fitBounds(bounds, {padding: [32, 32], maxZoom: 14});
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    window.gdo.onlineUsersMap.gdo_init();
});
