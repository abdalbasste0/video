// خبير النشر: إشعارك بالعمل الجاهز (تيليجرام + إشعار الجهاز) والنشر على يوتيوب بعد موافقتك فقط
import { Settings, Store } from './store.js';

export async function notifyReview(p) {
  const s = Settings.get();
  const title = p.publish?.title || p.script?.title || 'فيديو جديد';
  const msgs = [];
  try {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('🎬 فيديو جاهز لمراجعتك', { body: title, icon: 'icons/icon-192.png', tag: p.id });
      msgs.push('إشعار الجهاز');
    }
  } catch { /* some platforms only allow notifications from a service worker */ }

  if (s.telegramToken && s.telegramChat) {
    const api = `https://api.telegram.org/bot${s.telegramToken}`;
    const caption = `🎬 فيديو جاهز لمراجعتك\n\n«${title}»\nالجودة: ${p.qa?.score ?? '-'}% — تقييم السيناريو ${p.critique?.average?.toFixed(1) ?? '-'}/10\n\nافتح التطبيق ← المراجعة للموافقة أو طلب تعديل. لن يُنشر شيء بدون موافقتك.`;
    const video = await Store.getBlob(p.videoKey);
    const thumb = await Store.getBlob(p.thumbKey);
    if (video && video.size < 49 * 1048576) {
      const fd = new FormData();
      fd.append('chat_id', s.telegramChat);
      fd.append('caption', caption);
      fd.append('supports_streaming', 'true');
      fd.append('video', video, `review-${p.id}.${video.type.includes('mp4') ? 'mp4' : 'webm'}`);
      if (thumb) fd.append('thumbnail', thumb, 'thumb.jpg');
      const r = await fetch(`${api}/sendVideo`, { method: 'POST', body: fd });
      if (!r.ok) throw new Error('Telegram ' + r.status + ' ' + (await r.text()).slice(0, 150));
    } else {
      const fd = new FormData();
      fd.append('chat_id', s.telegramChat);
      fd.append('caption', caption + '\n(الفيديو أكبر من حد تيليجرام، شاهده في التطبيق)');
      if (thumb) fd.append('photo', thumb, 'thumb.jpg');
      const r = await fetch(`${api}/${thumb ? 'sendPhoto' : 'sendMessage'}`, { method: 'POST', body: thumb ? fd : JSON.stringify({ chat_id: s.telegramChat, text: caption }), headers: thumb ? undefined : { 'Content-Type': 'application/json' } });
      if (!r.ok) throw new Error('Telegram ' + r.status);
    }
    msgs.push('تيليجرام');
  }
  return msgs.length ? `أرسلت لك العمل للمراجعة عبر: ${msgs.join(' + ')}` : null;
}

export async function testTelegram() {
  const s = Settings.get();
  const r = await fetch(`https://api.telegram.org/bot${s.telegramToken}/sendMessage`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: s.telegramChat, text: '✅ مصنع الفيديو متصل! ستصلك هنا الفيديوهات الجاهزة للمراجعة.' }),
  });
  if (!r.ok) throw new Error((await r.text()).slice(0, 200));
}

// ---------- YouTube (OAuth via Google Identity Services, upload via resumable API) ----------
function loadGIS() {
  if (window.google?.accounts?.oauth2) return Promise.resolve();
  return new Promise((res, rej) => {
    const sc = document.createElement('script');
    sc.src = 'https://accounts.google.com/gsi/client';
    sc.onload = res; sc.onerror = () => rej(new Error('تعذر تحميل مكتبة Google'));
    document.head.appendChild(sc);
  });
}

let ytToken = null;
async function getYouTubeToken() {
  const s = Settings.get();
  if (!s.youtubeClientId) throw new Error('أضف Google OAuth Client ID في الإعدادات أولًا');
  if (ytToken && ytToken.exp > Date.now() + 60000) return ytToken.value;
  await loadGIS();
  return new Promise((resolve, reject) => {
    const client = window.google.accounts.oauth2.initTokenClient({
      client_id: s.youtubeClientId,
      scope: 'https://www.googleapis.com/auth/youtube.upload',
      callback: (resp) => {
        if (resp.error) return reject(new Error(resp.error_description || resp.error));
        ytToken = { value: resp.access_token, exp: Date.now() + resp.expires_in * 1000 };
        resolve(resp.access_token);
      },
    });
    client.requestAccessToken();
  });
}

export async function uploadToYouTube(p, { onProgress } = {}) {
  if (p.status !== 'approved') throw new Error('لا يمكن النشر قبل موافقتك');
  const s = Settings.get();
  const token = await getYouTubeToken();
  const video = await Store.getBlob(p.videoKey);
  const meta = {
    snippet: {
      title: p.publish.title.slice(0, 100),
      description: p.publish.description.slice(0, 4900),
      tags: p.publish.tags.slice(0, 30),
      categoryId: '24',
      defaultLanguage: p.brief.dialect === 'en' ? 'en' : 'ar',
    },
    status: { privacyStatus: s.youtubePrivacy || 'public', selfDeclaredMadeForKids: false, containsSyntheticMedia: true },
  };
  const init = await fetch('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json; charset=UTF-8', 'X-Upload-Content-Type': video.type, 'X-Upload-Content-Length': String(video.size) },
    body: JSON.stringify(meta),
  });
  if (!init.ok) throw new Error('YouTube init ' + init.status + ' ' + (await init.text()).slice(0, 200));
  const url = init.headers.get('Location');
  const res = await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', video.type);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total);
    xhr.onload = () => (xhr.status < 300 ? resolve(JSON.parse(xhr.responseText)) : reject(new Error('YouTube upload ' + xhr.status + ' ' + xhr.responseText.slice(0, 200))));
    xhr.onerror = () => reject(new Error('انقطع الاتصال أثناء الرفع'));
    xhr.send(video);
  });
  // custom thumbnail (requires a verified channel; ignore failure)
  try {
    const thumb = await Store.getBlob(p.thumbKey);
    if (thumb && p.brief.format !== 'short') {
      await fetch(`https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=${res.id}`, { method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'image/jpeg' }, body: thumb });
    }
  } catch { /* optional */ }
  return { id: res.id, url: `https://youtu.be/${res.id}` };
}

export async function downloadBlob(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 30000);
}
