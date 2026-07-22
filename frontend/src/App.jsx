import { useState } from 'react'
import Landing from './Landing.jsx'
import Dashboard from './Dashboard.jsx'

export default function App() {
  const [view, setView] = useState('landing')

  return view === 'landing' ? (
    <Landing onStart={() => setView('dashboard')} />
  ) : (
    <Dashboard onBack={() => setView('landing')} />
  )
}