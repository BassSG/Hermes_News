const state = { data: null, filter: 'all', search: '', deferredInstall: null };
const palette = {
  politics: ['#ff5d73', '#7c2dff'], business: ['#ffc857', '#1f9d8a'], world: ['#5aa8ff', '#9c7cff'],
  tech: ['#39d8ff', '#2364ff'], culture: ['#ff8bd1', '#7c2dff'], thailand: ['#53e3a6', '#39d8ff'], breaking: ['#ff5d73', '#ffc857'], default: ['#5aa8ff', '#9c7cff']
};
const $ = (id) => document.getElementById(id);
const fmt = new Intl.DateTimeFormat('th-TH', { dateStyle: 'medium', timeStyle: 'short' });

function visualFor(story) {
  const key = story.is_breaking ? 'breaking' : (story.category || 'default');
  const [a,b] = palette[key] || palette.default;
  const seed = [...story.title].reduce((n,c)=> n + c.charCodeAt(0), 0) % 360;
  return `radial-gradient(circle at 18% 16%, ${a} 0, transparent 34%), radial-gradient(circle at 88% 18%, ${b} 0, transparent 30%), linear-gradient(${seed}deg, rgba(255,255,255,.18), rgba(255,255,255,0)), #101e34`;
}
function categoryLabel(cat) {
  return ({politics:'การเมือง', business:'เศรษฐกิจ', world:'ต่างประเทศ', tech:'เทค', culture:'ไลฟ์/กีฬา', thailand:'ไทย', general:'ทั่วไป'})[cat] || 'ทั่วไป';
}
function timeAgo(iso) {
  const t = new Date(iso).getTime();
  if (!Number.isFinite(t)) return '';
  const diff = Date.now() - t;
  const mins = Math.max(1, Math.round(diff / 60000));
  if (mins < 60) return `${mins} นาทีที่แล้ว`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} ชม.ที่แล้ว`;
  return `${Math.round(hrs/24)} วันที่แล้ว`;
}
function card(story, lead=false) {
  const el = document.createElement('article');
  el.className = 'news-card';
  el.style.setProperty('--visual', visualFor(story));
  el.tabIndex = 0;
  el.setAttribute('role', 'button');
  el.setAttribute('aria-label', `เปิดรายละเอียด ${story.title}`);
  el.innerHTML = `
    <div class="card-topline">
      <span class="pill">${story.is_breaking ? 'ด่วน/ดัง' : categoryLabel(story.category)}</span>
      <span class="pill score-pill">Impact ${story.score}</span>
    </div>
    <h3>${escapeHtml(story.title)}</h3>
    <p>${escapeHtml(story.summary || story.description || 'อ่านรายละเอียดเพิ่มเติมจากแหล่งข่าวต้นทาง')}</p>
    <div class="card-footer">
      <span>${escapeHtml(story.source || 'Google News')} • ${timeAgo(story.published_at)}</span>
      <span class="open-link">เปิดอ่าน →</span>
    </div>`;
  el.addEventListener('click', () => openStory(story.id));
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter') openStory(story.id); });
  return el;
}
function escapeHtml(str='') { return String(str).replace(/[&<>'"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[s])); }
function filteredStories() {
  const q = state.search.trim().toLowerCase();
  return (state.data?.stories || []).filter(s => {
    const byFilter = state.filter === 'all' || (state.filter === 'breaking' ? s.is_breaking : s.category === state.filter || (state.filter === 'thailand' && s.country_focus === 'TH'));
    const bySearch = !q || `${s.title} ${s.summary} ${s.source}`.toLowerCase().includes(q);
    return byFilter && bySearch;
  });
}
function render() {
  if (!state.data) return;
  $('totalStories').textContent = state.data.stories.length;
  const updated = state.data.generated_at ? fmt.format(new Date(state.data.generated_at)) : 'ไม่ทราบเวลา';
  $('briefMeta').textContent = `อัปเดต ${updated} • คัดจาก ${state.data.sources.length} feed • เรียงตามความดัง/ผลกระทบ`;
  $('updatedBadge').textContent = state.data.is_live ? 'LIVE RSS' : 'DEMO';

  const leads = state.data.stories.slice(0, 3);
  $('leadGrid').replaceChildren(...leads.map((s,i)=>card(s, i===0)));
  const stories = filteredStories();
  $('newsGrid').replaceChildren(...stories.map(s=>card(s)));
  $('emptyState').hidden = stories.length > 0;

  const commandItems = buildCommandItems(state.data.stories);
  $('commandList').innerHTML = commandItems.map(item => `<div class="command-item"><strong>${item.title}</strong><p>${item.text}</p></div>`).join('');
}
function buildCommandItems(stories) {
  const top = stories[0];
  const th = stories.filter(s => s.country_focus === 'TH').length;
  const world = stories.filter(s => s.category === 'world').length;
  const biz = stories.find(s => s.category === 'business');
  const pol = stories.find(s => s.category === 'politics');
  return [
    { title: 'Top Watch', text: top ? top.title : 'ยังไม่มีข่าวเด่น' },
    { title: 'Thailand Pulse', text: `มีข่าวไทย ${th} เรื่องใน brief นี้ — เน้นเรื่องที่กระทบคนส่วนใหญ่ก่อน` },
    { title: 'Policy / Economy', text: (pol || biz)?.title || 'ยังไม่มีประเด็นนโยบาย/เศรษฐกิจเด่น' },
    { title: 'Global Watch', text: world ? `มีข่าวต่างประเทศสำคัญ ${world} เรื่องแซมใน feed` : 'รอบนี้ยังไม่มีข่าวต่างประเทศที่คะแนนสูงพอ' }
  ];
}
function openStory(id) {
  const story = state.data.stories.find(s => s.id === id);
  if (!story) return;
  location.hash = `story-${id}`;
  $('dialogVisual').style.setProperty('--visual', visualFor(story));
  $('dialogMeta').innerHTML = `<span class="pill">${categoryLabel(story.category)}</span><span class="pill">${escapeHtml(story.source || '')}</span><span class="pill score-pill">Impact ${story.score}</span><span class="pill">${timeAgo(story.published_at)}</span>`;
  $('dialogTitle').textContent = story.title;
  $('dialogSummary').textContent = story.summary || story.description || 'อ่านรายละเอียดเพิ่มเติมจากแหล่งข่าวต้นทาง';
  $('dialogWhy').textContent = story.why_it_matters || inferWhy(story);
  $('sourceLink').href = story.link;
  $('storyDialog').showModal();
}
function inferWhy(story) {
  if (story.category === 'politics') return 'ประเด็นนี้อาจกระทบการตัดสินใจเชิงนโยบาย กฎหมาย หรือบรรยากาศสังคมในไทย';
  if (story.category === 'business') return 'ประเด็นนี้อาจกระทบค่าครองชีพ ตลาด เงินบาท พลังงาน หรือธุรกิจในประเทศ';
  if (story.category === 'world') return 'เป็นข่าวต่างประเทศที่อาจมีผลต่อภูมิรัฐศาสตร์ เศรษฐกิจโลก หรือ sentiment ในไทย';
  return 'เป็นเรื่องที่กำลังถูกพูดถึงและควรรู้เพื่อไม่ตกกระแสข่าวเช้า';
}
async function loadData() {
  const res = await fetch(`data/news.json?ts=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`data/news.json ${res.status}`);
  state.data = await res.json();
  render();
}

document.addEventListener('DOMContentLoaded', async () => {
  document.querySelectorAll('.filter').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); state.filter = btn.dataset.filter; render();
  }));
  $('searchInput').addEventListener('input', (e) => { state.search = e.target.value; render(); });
  $('refreshBtn').addEventListener('click', () => loadData());
  $('closeDialog').addEventListener('click', () => $('storyDialog').close());
  $('copyLinkBtn').addEventListener('click', async () => { await navigator.clipboard.writeText($('sourceLink').href); $('copyLinkBtn').textContent='คัดลอกแล้ว'; setTimeout(()=>$('copyLinkBtn').textContent='คัดลอกลิงก์', 1400); });
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); state.deferredInstall = e; $('installBtn').hidden = false; });
  $('installBtn').addEventListener('click', async () => { if (state.deferredInstall) { state.deferredInstall.prompt(); state.deferredInstall = null; $('installBtn').hidden = true; } });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('service-worker.js').catch(console.warn);
  try { await loadData(); } catch (err) { $('briefMeta').textContent = `โหลดข้อมูลไม่ได้: ${err.message}`; }
});
