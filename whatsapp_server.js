/**
 * WhatsApp Web server for DeliveryBillApp
 *
 * Wraps whatsapp-web.js in a tiny Express HTTP server on localhost:3000.
 * Python calls this server to send messages — no browser window manipulation,
 * no keyboard tricks, fully background.
 *
 * Endpoints:
 *   GET  /status        → { state, qr }
 *   POST /send          → { phone, message }  →  { ok, error? }
 *   POST /logout        → {} → { ok }
 *   POST /stop          → {} → shuts server down
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const fs = require('fs');
const path = require('path');

// ── Self-contained log (always written regardless of Python's stdout redirect) ─
const _logStream = fs.createWriteStream(
    path.join(__dirname, 'whatsapp_node.log'), { flags: 'a' }
);

const app = express();
app.use(express.json({ limit: '10mb' }));

// ── State ─────────────────────────────────────────────────────────────────────
let client = null;
let state  = 'initializing';   // initializing | qr | authenticated | ready | disconnected | error
let qrString = null;

// ── Helpers ───────────────────────────────────────────────────────────────────
function log(msg) {
    const line = new Date().toISOString() + ' ' + msg + '\n';
    process.stdout.write(line);
    try { _logStream.write(line); } catch(e) {}
}

function findChrome() {
    const candidates = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        // Chrome for Testing / user-level installs
        process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
        process.env.PROGRAMFILES + '\\Google\\Chrome\\Application\\chrome.exe',
        // Edge as a fallback (Chromium-based, works with Puppeteer)
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    ];
    for (const p of candidates) {
        if (p && fs.existsSync(p)) return p;
    }
    // Last resort: let Puppeteer find it via its own detection
    return undefined;
}

// ── WhatsApp client ───────────────────────────────────────────────────────────
let _reconnectTimer   = null;
let _logoutInProgress = false;

function scheduleReconnect(delayMs) {
    if (_reconnectTimer) clearTimeout(_reconnectTimer);
    _reconnectTimer = setTimeout(() => {
        _reconnectTimer = null;
        initClient();
    }, delayMs);
}

async function initClient() {
    // Destroy the old client cleanly before creating a new one
    if (client) {
        const old = client;
        client = null;
        try { await old.destroy(); } catch (e) { log('DESTROY_WARN:' + e.message); }
    }

    state    = 'initializing';
    qrString = null;

    const sessionDir   = path.join(__dirname, 'whatsapp_session');
    const chromeExe    = findChrome();

    log('CHROME_PATH:' + (chromeExe || 'using puppeteer default'));

    client = new Client({
        authStrategy: new LocalAuth({
            dataPath: sessionDir,
            clientId: 'deliverybillapp',
        }),
        puppeteer: {
            headless: true,
            executablePath: chromeExe,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--window-size=1280,720',
            ],
        },
    });

    log('CLIENT_CREATED');

    client.on('qr', (qr) => {
        state    = 'qr';
        qrString = qr;
        log('QR:' + qr);
    });

    client.on('authenticated', () => {
        state    = 'authenticated';
        qrString = null;
        log('AUTHENTICATED');
    });

    client.on('ready', () => {
        state    = 'ready';
        qrString = null;
        log('READY');
    });

    client.on('disconnected', (reason) => {
        state    = 'disconnected';
        qrString = null;
        log('DISCONNECTED:' + (reason || ''));
        // Don't double-schedule during an explicit logout
        if (!_logoutInProgress) {
            scheduleReconnect(4000);
        }
    });

    client.on('auth_failure', (msg) => {
        state = 'error';
        log('AUTH_FAILURE:' + msg);
        if (!_logoutInProgress) scheduleReconnect(6000);
    });

    client.initialize().catch((err) => {
        state = 'error';
        log('INIT_ERROR:' + err.message);
        if (!_logoutInProgress) scheduleReconnect(8000);
    });
}

// ── REST API ──────────────────────────────────────────────────────────────────
app.get('/status', (req, res) => {
    res.json({ state, qr: qrString });
});

app.post('/send', async (req, res) => {
    if (state !== 'ready') {
        return res.status(503).json({
            ok: false,
            error: 'WhatsApp not connected. Current state: ' + state,
        });
    }

    const { phone, message } = req.body || {};
    if (!phone || !message) {
        return res.status(400).json({ ok: false, error: '"phone" and "message" are required.' });
    }

    try {
        // whatsapp-web.js format: strip + and append @c.us
        const chatId = phone.replace(/^\+/, '') + '@c.us';
        await client.sendMessage(chatId, String(message));
        log('SENT:' + phone);
        res.json({ ok: true });
    } catch (err) {
        log('SEND_ERROR:' + phone + ':' + err.message);
        res.status(500).json({ ok: false, error: err.message });
    }
});

app.post('/logout', async (req, res) => {
    try {
        _logoutInProgress = true;
        if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
        if (client) await client.logout().catch(() => {});
        state    = 'disconnected';
        qrString = null;
        log('LOGGED_OUT');
        res.json({ ok: true });
        _logoutInProgress = false;
        scheduleReconnect(2000);
    } catch (err) {
        _logoutInProgress = false;
        res.status(500).json({ ok: false, error: err.message });
    }
});

app.post('/reconnect', (req, res) => {
    log('RECONNECT_REQUESTED');
    scheduleReconnect(500);
    res.json({ ok: true });
});

app.post('/stop', (req, res) => {
    res.json({ ok: true });
    log('STOPPING');
    setTimeout(() => process.exit(0), 400);
});

// ── Start ─────────────────────────────────────────────────────────────────────
const PORT = 3000;
app.listen(PORT, '127.0.0.1', () => {
    log('SERVER_READY:' + PORT);
    initClient();
});

function shutdown() {
    log('SHUTDOWN');
    const done = () => process.exit(0);
    if (client) client.destroy().then(done).catch(done);
    else done();
}
process.on('SIGTERM', shutdown);
process.on('SIGINT',  shutdown);
