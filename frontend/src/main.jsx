import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <h1>Can't have ESLint errors if the app doesn't exist</h1>
  </StrictMode>,
);