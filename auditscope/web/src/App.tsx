import { Routes, Route, Navigate } from 'react-router-dom'
import { Home } from './pages/Home'
import { SearchResults } from './pages/SearchResults'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/search" element={<SearchResults />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
