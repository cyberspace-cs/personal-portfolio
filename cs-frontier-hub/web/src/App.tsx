import { useEffect, useState } from 'react'
import { ThemeProvider } from './context/ThemeContext'
import { Navbar } from './components/Navbar'
import { Footer } from './components/Footer'
import { Home } from './pages/Home'
import { Detail } from './pages/Detail'
import { Favorites } from './pages/Favorites'
import { Admin } from './pages/Admin'

function useHash() {
  const parse = () => {
    const h = window.location.hash.replace(/^#\/?/, '')
    const [route, param] = h.split('/')
    return { route: route || '', param: param || '' }
  }
  const [hash, setHash] = useState(parse)
  useEffect(() => {
    const onHash = () => setHash(parse())
    window.addEventListener('hashchange', onHash)
    if (!window.location.hash) window.location.hash = '#/'
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  return hash
}

export default function App() {
  const { route, param } = useHash()
  return (
    <ThemeProvider>
      <Navbar route={route} />
      <main>
        {route === '' && <Home />}
        {route === 'item' && <Detail slug={param} />}
        {route === 'favorites' && <Favorites />}
        {route === 'admin' && <Admin />}
        {!['', 'item', 'favorites', 'admin'].includes(route) && (
          <div className="mx-auto max-w-4xl px-4 py-16 text-center text-muted">
            页面不存在。<a href="#/" className="text-accent underline">返回首页</a>
          </div>
        )}
      </main>
      <Footer />
    </ThemeProvider>
  )
}
