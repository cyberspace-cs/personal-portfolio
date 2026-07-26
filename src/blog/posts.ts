// 构建期加载 src/blog/content/*.md（原始文本），解析 frontmatter，供列表/文章页使用。
export interface PostMeta {
  slug: string;
  title: string;
  date: string;
  tags: string[];
  excerpt: string;
  content: string; // 去掉 frontmatter 后的 markdown 正文
}

// Vite 构建期静态分析：eager 同步加载，?raw 取原始字符串
const modules = import.meta.glob('./content/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

interface Frontmatter {
  [key: string]: string | string[];
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
    } else {
      meta[key] = val;
    }
  }
  return { meta, body };
}

function asString(v: string | string[] | undefined, fallback = ''): string {
  if (Array.isArray(v)) return v.join(', ');
  return v ?? fallback;
}

export const posts: PostMeta[] = Object.entries(modules)
  .map(([path, raw]) => {
    const slug = path.split('/').pop()!.replace(/\.md$/, '');
    const { meta, body } = parseFrontmatter(raw);
    return {
      slug,
      title: asString(meta.title, slug),
      date: asString(meta.date, ''),
      tags: Array.isArray(meta.tags) ? meta.tags : [],
      excerpt: asString(meta.excerpt, ''),
      content: body,
    };
  })
  // 按日期倒序（新→旧）；无日期排最后
  .sort((a, b) => {
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
