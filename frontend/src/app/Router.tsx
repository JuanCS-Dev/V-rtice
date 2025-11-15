import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
  Outlet,
} from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

// Layouts
import { MainLayout } from "@/components/layout/MainLayout";

// Pages (lazy loaded)
import { lazy, Suspense } from "react";
import { LoadingSpinner } from "@/components/ui";

const HomePage = lazy(() => import("@/pages/Home/HomePage"));
const LoginPage = lazy(() => import("@/pages/Auth/LoginPage"));
const DashboardPage = lazy(() => import("@/pages/Dashboard/DashboardPage"));
const OffensivePage = lazy(() => import("@/pages/Offensive/OffensivePage"));
const DefensivePage = lazy(() => import("@/pages/Defensive/DefensivePage"));
const OSINTPage = lazy(() => import("@/pages/OSINT/OSINTPage"));
const MaximusPage = lazy(() => import("@/pages/Maximus/MaximusPage"));
const ImmunisPage = lazy(() => import("@/pages/Immunis/ImmunisPage"));
const ReactiveFabricPage = lazy(
  () => import("@/pages/ReactiveFabric/ReactiveFabricPage"),
);
const SINESPPage = lazy(() => import("@/pages/SINESP/SINESPPage"));
const AdminPage = lazy(() => import("@/pages/Admin/AdminPage"));
const SettingsPage = lazy(() => import("@/pages/Settings/SettingsPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFound/NotFoundPage"));

// Loading fallback
const PageLoader = () => (
  <div className="flex h-screen items-center justify-center">
    <LoadingSpinner size="lg" label="Loading page..." />
  </div>
);

// Protected Route wrapper
interface ProtectedRouteProps {
  roles?: string[];
}

function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (roles && user && !roles.some((role) => user.roles.includes(role))) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

// Router configuration
const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          {
            path: "dashboard",
            element: <DashboardPage />,
          },
          {
            path: "offensive",
            element: <ProtectedRoute roles={["admin", "offensive"]} />,
            children: [
              {
                index: true,
                element: <OffensivePage />,
              },
            ],
          },
          {
            path: "defensive",
            element: <DefensivePage />,
          },
          {
            path: "osint",
            element: <OSINTPage />,
          },
          {
            path: "maximus",
            element: <MaximusPage />,
          },
          {
            path: "immunis",
            element: <ImmunisPage />,
          },
          {
            path: "reactive-fabric",
            element: <ReactiveFabricPage />,
          },
          {
            path: "sinesp",
            element: <SINESPPage />,
          },
          {
            path: "admin",
            element: <ProtectedRoute roles={["admin"]} />,
            children: [
              {
                index: true,
                element: <AdminPage />,
              },
            ],
          },
          {
            path: "settings",
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);

export function AppRouter() {
  return (
    <Suspense fallback={<PageLoader />}>
      <RouterProvider router={router} />
    </Suspense>
  );
}
