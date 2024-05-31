import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './main'

const container = document.getElementById('root')
if (container) {
  const root2 = createRoot(container)
  root2.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
}
