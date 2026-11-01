import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import Home from './pages/Home'

// Portal pages pull in Chart.js — load them on demand to keep the landing page light
const AgentsLive = lazy(() => import('./pages/AgentsLive'))
const Clinician = lazy(() => import('./pages/Clinician'))
const Caregiver = lazy(() => import('./pages/Caregiver'))
const Patient = lazy(() => import('./pages/Patient'))

const page = (C) => <Suspense fallback={<Loading height={240} />}><C /></Suspense>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route element={<Layout />}>
        <Route path="/agents" element={page(AgentsLive)} />
        <Route path="/clinician" element={page(Clinician)} />
        <Route path="/caregiver" element={page(Caregiver)} />
        <Route path="/patient" element={page(Patient)} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
