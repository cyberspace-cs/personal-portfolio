import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { useLanguage } from '../context/LanguageContext';
import { getPost, readingMinutes } from './posts';
import 'highlight.js/styles/github-dark.css';

function formatDate(d: string): string {
  if (!d) return '';
  return d.replace(/-/g, '.');
}

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>();
  const { t } = useLanguage();
  const post = slug ? getPost(slug) : undefined;

  if (!post) {
    return (
      <div className="max-w-3xl mx-auto px-4 pt-32 pb-20 text-center">
        <h1 className="text-2xl font-bold text-fg">404</h1>
        <p className="mt-3 text-muted">{t.blogEmpty}</p>
        <Link to="/blog" className="mt-6 inline-block text-accent hover:text-accent-2">
          ← {t.blogBack}
        </Link>
      </div>
    );
  }

  const minutes = readingMinutes(post.content);

  return (
    <article className="max-w-3xl mx-auto px-4 sm:px-6 pt-28 pb-20">
      <Link
        to="/blog"
        className="inline-flex items-center gap-1 text-sm text-muted hover:text-accent transition-colors duration-200"
      >
        ← {t.blogBack}
      </Link>

      {/* 标题区 */}
      <header className="mt-6 mb-8 border-b border-line pb-8">
        <div className="flex flex-wrap items-center gap-2 text-xs text-faint mb-4">
          {post.date && (
            <span>
              {t.blogPublished} {formatDate(post.date)}
            </span>
          )}
          <span>·</span>
          <span>
            {minutes} {t.blogMinRead}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold leading-tight text-fg">
          {post.title}
        </h1>
        {post.tags.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-surface-2 px-3 py-1 text-xs text-muted"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* 正文 */}
      <div className="blog-prose">
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
          {post.content}
        </ReactMarkdown>
      </div>

      {/* 底部返回 */}
      <div className="mt-14 border-t border-line pt-8">
        <Link
          to="/blog"
          className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-accent-2 transition-colors duration-200"
        >
          ← {t.blogBack}
        </Link>
      </div>
    </article>
  );
}
