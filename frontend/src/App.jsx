import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { RouterProvider } from 'react-router-dom';

import { AuthProvider } from './context/AuthContext.jsx';
import queryClient from './api/queryClient.js';
import router from './router.jsx';

export default function App() {
  return (
    // 1. AuthProvider — manages user state and the JWT lifecycle.
    //    Must sit above RouterProvider so ProtectedRoute can read auth state.
    <AuthProvider>
      {/* 2. QueryClientProvider — makes TanStack Query available everywhere. */}
      <QueryClientProvider client={queryClient}>
        {/* 3. RouterProvider — renders the matched page component. */}
        <RouterProvider router={router} />
        {/* DevTools panel — only visible in development builds. */}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </AuthProvider>
  );
}