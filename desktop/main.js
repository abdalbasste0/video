// Desktop wrapper (Windows / macOS / Linux): serves the app from a local server and opens it in a window.
const { app, BrowserWindow, shell } = require('electron');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = app.isPackaged ? path.join(process.resourcesPath, 'app') : path.join(__dirname, '..', 'app');
const PORT = 47821; // fixed so saved projects (IndexedDB) stay attached to the same origin
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.svg': 'image/svg+xml' };

function serve() {
  return new Promise((resolve, reject) => {
    const srv = http.createServer((req, res) => {
      const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/+/, '') || 'index.html';
      const file = path.normalize(path.join(ROOT, rel));
      if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); return res.end('not found'); }
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
        res.end(data);
      });
    });
    srv.on('error', reject);
    srv.listen(PORT, '127.0.0.1', () => resolve(`http://127.0.0.1:${PORT}/`));
  });
}

async function createWindow() {
  const url = await serve();
  const win = new BrowserWindow({
    width: 1280, height: 860, backgroundColor: '#0b0b0f', title: 'مصنع الرعب', autoHideMenuBar: true,
    icon: path.join(ROOT, 'icons', 'icon-512.png'),
    webPreferences: { backgroundThrottling: false }, // keep rendering videos when minimised
  });
  win.webContents.setWindowOpenHandler(({ url: u }) => { shell.openExternal(u); return { action: 'deny' }; });
  win.loadURL(url);
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
