import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './hooks/useAuth.js';

// Pages — loaded eagerly for simplicity. In a larger app you'd lazy-load
// these with React.lazy() + Suspense to improve the initial bundle size.
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import LogHistory from './pages/LogHistory.jsx';
import GeoMap from './pages/GeoMap.jsx';
import Analytics from './pages/Analytics.jsx';
import Anomalies from './pages/Anomalies.jsx';
import ApiKeys from './pages/ApiKeys.jsx';

// ---------------------------------------------------------------------------
// ProtectedRoute — redirects unauthenticated users to /login.
// Shows nothing while we're still resolving the session on first load.
// ---------------------------------------------------------------------------
function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    // Avoid a flash of the login page while we attempt a silent refresh.
    return null;
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    // All dashboard routes are children of the ProtectedRoute guard.
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <Dashboard />,
      },
      {
        path: '/logs',
        element: <LogHistory />,
      },
      {
        path: '/geo',
        element: <GeoMap />,
      },
      {
        path: '/analytics',
        element: <Analytics />,
      },
      {
        path: '/anomalies',
        element: <Anomalies />,
      },
      {
        path: '/api-keys',
        element: <ApiKeys />,
      },
      {
        // Catch-all: redirect unknown paths to the dashboard.
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

export default router;