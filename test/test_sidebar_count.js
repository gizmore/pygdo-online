const assert = require('node:assert/strict');
const test = require('node:test');

test('refreshes online and viewer counts in the sidebar label', async () => {
    const node = {nodeValue: '12(+1) Online, (0 watch)'};
    const link = {dataset: {onlineCounter: '12', onlineGuests: '1', onlineViewers: '0', onlineCountUrl: '/count'}};
    global.window = {};
    global.NodeFilter = {SHOW_TEXT: 4};
    global.document = {
        addEventListener() {},
        querySelector: () => link,
        createTreeWalker: () => ({currentNode: node, nextNode: (() => { let first = true; return () => { const result = first; first = false; return result; }; })()}),
    };
    global.fetch = async () => ({ok: true, json: async () => ({data: {users: 13, guests: 2, stream_viewers: 4}})});
    require('../js/pygdo-online.js');
    await window.gdo.online.refreshCount();
    assert.equal(node.nodeValue, '13(+2) Online, (4 watch)');
    assert.equal(link.dataset.onlineViewers, '4');
});
