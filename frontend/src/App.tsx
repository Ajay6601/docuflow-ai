import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { DocumentDetail } from './pages/DocumentDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App