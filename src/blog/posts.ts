// 构建期加载 src/blog/content/*.md（原始文本），解析 frontmatter，供列表/文章页使用。
export interface PostMeta {
  slug: string;
  title: string;
  date: string;
  tags: string[];
  excerpt: string;
  content: string; // 去掉 frontmatter 后的 markdown 正文
  order?: number; // 同系列内的阅读顺序（升序）；缺省按日期倒序
  series?: string; // 系列名（用于列表分组/标识）
}

// Vite 构建期静态分析：eager 同步加载，?raw 取原始字符串
const modules = import.meta.glob('./content/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

interface Frontmatter {
  [key: string]: string | string[] | number;
}

function parseFrontmatter(raw: string): { meta: Frontmatter; body: string } {
  const m = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: raw };
  const fmBlock = m[1];
  const body = m[2];
  const meta: Frontmatter = {};
  for (const line of fmBlock.split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let val = line.slice(idx + 1).trim();
    val = val.replace(/^["']|["']$/g, '');
    if (val.startsWith('[') && val.endsWith(']')) {
      meta[key] = val
        .slice(1, -1)
        .split(',')
        .map((s) => s.trim().replace(/^["']|["']$/g, ''))
        .filter(Boolean);
    } else if (key === 'order') {
      const n = Number(val);
      meta[key] = isNaN(n) ? val : n;
    } else {
      meta[key] = val;
    }
  }
  return { meta, body };
}

function asString(v: string | string[] | number | undefined, fallback = ''): string {
  if (Array.isArray(v)) return v.join(', ');
  if (typeof v === 'number') return String(v);
  return v ?? fallback;
}

export const posts: PostMeta[] = Object.entries(modules)
  .map(([path, raw]) => {
    const slug = path.split('/').pop()!.replace(/\.md$/, '');
    const { meta, body } = parseFrontmatter(raw);
    const orderVal = meta.order;
    return {
      slug,
      title: asString(meta.title, slug),
      date: asString(meta.date, ''),
      tags: Array.isArray(meta.tags) ? (meta.tags as string[]) : [],
      excerpt: asString(meta.excerpt, ''),
      content: body,
      order: typeof orderVal === 'number' ? orderVal : undefined,
      series: asString(meta.series, '') || undefined,
    };
  })
  // 有 order 的按 order 升序（系列内部顺序）；其余按日期倒序
  .sort((a, b) => {
    const oa = a.order;
    const ob = b.order;
    if (oa != null && ob != null) return oa - ob;
    if (oa != null) return -1;
    if (ob != null) return 1;
    if (!a.date && !b.date) return a.title.localeCompare(b.title);
    if (!a.date) return 1;
    if (!b.date) return -1;
    return a.date < b.date ? 1 : -1;
  });

export function getPost(slug: string): PostMeta | undefined {
  return posts.find((p) => p.slug === slug);
}

// 粗略阅读时长（中文按 ~400 字/分钟）
export function readingMinutes(content: string): number {
  const chars = content.replace(/\s+/g, '').length;
  return Math.max(1, Math.round(chars / 400));
}
