// Vercel 无服务函数：把 aihot 公开接口代理给前端。
// 前端（部署在 Vercel 同域）因 CORS 无法直接调用 aihot，故由本函数同源代理。
// 路由：
//   /api/aihot/daily         -> https://aihot.virxact.com/api/public/daily
//   /api/aihot/daily?date=YYYY-MM-DD -> .../daily/YYYY-MM-DD
//   /api/aihot/dailies?take=180       -> .../dailies?take=180
const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const BASE = 'https://aihot.virxact.com';

export default async function handler(req, res) {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const parts = req.query.splat || req.query.slug || [];
    let path = Array.isArray(parts) ? parts.join('/') : String(parts || '');
    if (!path) {
      res.status(400).json({ error: 'missing path' });
      return;
    }

    // aihot 只认 path 形式的日期：/api/public/daily/YYYY-MM-DD
    // 而前端习惯用 ?date= 查询，这里把 date 转成 path 段，其余参数（take 等）透传
    const upstreamQuery = new URLSearchParams(url.searchParams);
    const date = upstreamQuery.get('date');
    if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
      upstreamQuery.delete('date');
      if (path === 'daily') path = `daily/${date}`;
    }
    const qs = upstreamQuery.toString();

    const target = `${BASE}/api/public/${path}${qs ? '?' + qs : ''}`;
    const upstream = await fetch(target, {
      headers: { 'User-Agent': UA, Accept: 'application/json' },
      redirect: 'follow',
    });
    const body = await upstream.text();
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
    res.status(upstream.status).send(body);
  } catch (e) {
    res.status(502).json({ error: String((e && e.message) || e) });
  }
}
