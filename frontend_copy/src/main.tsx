import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { App } from './ui/App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="min-h-screen bg-slate-50">
      <App />
    </div>
  </React.StrictMode>,
) 