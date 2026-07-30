import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { posts } from './posts';

function formatDate(d: string): string {
  if (!d) return '';
  // 2026-07-26 -> 2026.07.26
  return d.replace(/-/g, '.');
}

export default function BlogList() {
  const { t } = useLanguage();

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-20">
      {/* 头部 */}
      <header className="mb-12">
        <div className="flex items-center gap-3 mb-3">
          <span className="h-1.5 w-8 rounded-full bg-accent" />
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-fg">
            {t.blogTitle}
          </h1>
        </div>
        <p className="text-muted text-base sm:text-lg max-w-2xl">{t.blogSubtitle}</p>
      </header>

      {/* 文章列表 */}
      {posts.length === 0 ? (
        <p className="text-muted">{t.blogEmpty}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              to={`/blog/${post.slug}`}
              className="group flex flex-col rounded-2xl border border-line bg-surface p-6 transition-all duration-300 hover:border-accent hover:shadow-lg hover:shadow-accent/5"
            >
              <div className="flex items-center gap-3 text-xs text-faint mb-3">
                {post.date && <span>{formatDate(post.date)}</span>}
                {post.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-surface-2 px-2.5 py-0.5 text-[11px] text-muted"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <h2 className="text-xl font-bold text-fg leading-snug group-hover:text-accent transition-colors duration-200">
                {post.title}
              </h2>

              <p className="mt-3 text-sm leading-relaxed text-muted line-clamp-4 flex-1">
                {post.excerpt}
              </p>

              <span className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-accent opacity-0 -translate-x-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
                {t.blogReading}
                <span className="text-faint">→</span>
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
