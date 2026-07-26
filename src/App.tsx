import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './components/Home';

// 博客模块按需加载，避免 react-markdown / highlight.js / 5 篇全文拖慢首页
const BlogList = lazy(() => import('./blog/BlogList'));
const BlogPost = lazy(() => import('./blog/BlogPost'));

function Loading() {
  return (
    <div className="max-w-3xl mx-auto px-4 pt-32 pb-20 text-center text-muted">
      Loading…
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-bg">
      <Navbar />
      <main>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/blog" element={<BlogList />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
