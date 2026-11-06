// التخزين المحلي: المشاريع والملفات (صور، صوت، فيديو) في IndexedDB، والإعدادات في localStorage
const DB_NAME = 'horror-factory';
const DB_VER = 1;
let dbPromise;

function db() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VER);
      req.onupgradeneeded = () => {
        const d = req.result;
        if (!d.objectStoreNames.contains('projects')) d.createObjectStore('projects', { keyPath: 'id' });
        if (!d.objectStoreNames.contains('blobs')) d.createObjectStore('blobs');
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbPromise;
}

async function tx(store, mode, fn) {
  const d = await db();
  return new Promise((resolve, reject) => {
    const t = d.transaction(store, mode);
    const s = t.objectStore(store);
    let result;
    Promise.resolve(fn(s)).then((r) => { result = r; });
    t.oncomplete = () => resolve(result);
    t.onerror = () => reject(t.error);
  });
}

function reqP(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export const Store = {
  async saveProject(p) {
    p.updatedAt = Date.now();
    await tx('projects', 'readwrite', (s) => s.put(structuredClone(p)));
    window.dispatchEvent(new CustomEvent('project-updated', { detail: p.id }));
  },
  async getProject(id) {
    return tx('projects', 'readonly', (s) => reqP(s.get(id)));
  },
  async listProjects() {
    const all = await tx('projects', 'readonly', (s) => reqP(s.getAll()));
    return (all || []).sort((a, b) => b.createdAt - a.createdAt);
  },
  async deleteProject(id) {
    const p = await this.getProject(id);
    if (p) {
      const keys = collectBlobKeys(p);
      await tx('blobs', 'readwrite', (s) => keys.forEach((k) => s.delete(k)));
    }
    await tx('projects', 'readwrite', (s) => s.delete(id));
    window.dispatchEvent(new CustomEvent('project-updated', { detail: id }));
  },
  async putBlob(key, blob) {
    await tx('blobs', 'readwrite', (s) => s.put(blob, key));
    return key;
  },
  async getBlob(key) {
    if (!key) return null;
    return tx('blobs', 'readonly', (s) => reqP(s.get(key)));
  },
};

function collectBlobKeys(p) {
  const keys = [];
  const walk = (o) => {
    if (!o || typeof o !== 'object') return;
    for (const [k, v] of Object.entries(o)) {
      if (typeof v === 'string' && /Key$/.test(k)) keys.push(v);
      else if (typeof v === 'object') walk(v);
    }
  };
  walk(p);
  return keys;
}

const SETTINGS_KEY = 'hf-settings';
export const DEFAULT_SETTINGS = {
  claudeKey: '',
  claudeModel: 'claude-opus-5-5',
  imageProvider: 'pollinations', // pollinations | openai | procedural
  openaiKey: '',
  elevenKey: '',
  elevenVoice: '',
  elevenModel: 'eleven_v3',
  qualityThreshold: 8.5,
  maxRevisions: 2,
  telegramToken: '',
  telegramChat: '',
  youtubeClientId: '',
  youtubePrivacy: 'public',
  channelName: '',
  renderQuality: '1080', // 1080 | 720
  defaultDialect: 'msa',
};

export const Settings = {
  get() {
    try {
      return { ...DEFAULT_SETTINGS, ...(JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}) };
    } catch {
      return { ...DEFAULT_SETTINGS };
    }
  },
  set(patch) {
    const next = { ...this.get(), ...patch };
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(next)); } catch { /* ignore */ }
    return next;
  },
};

export const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
