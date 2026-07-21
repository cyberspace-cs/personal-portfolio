import { Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { Footer } from './components/Footer'
import { AuthModal } from './components/AuthModal'
import { UIProvider, useUI } from './lib/ui'
import { HomePage } from './pages/HomePage'
import { CompetitionDetail } from './pages/CompetitionDetail'
import { FavoritesPage } from './pages/FavoritesPage'
import { SubmitPage } from './pages/SubmitPage'
import { NotFound } from './pages/NotFound'

function Toast() {
  const { message } = useUI()
  if (!message) return null
  return (
    <div className="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2">
      <div
        className={`rounded-xl border px-4 py-2 text-sm shadow-lg backdrop-blur ${
          message.kind === 'ok'
            ? 'border-neon-green/40 bg-neon-green/15 text-neon-green'
            : 'border-neon-pink/40 bg-neon-pink/15 text-neon-pink'
        }`}
      >
        {message.text}
      </div>
    </div>
  )
}

function Shell() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/competition/:id" element={<CompetitionDetail />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/submit" element={<SubmitPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <AuthModal />
      <Toast />
    </div>
  )
}

export default function App() {
  return (
    <UIProvider>
      <Shell />
    </UIProvider>
  )
}
