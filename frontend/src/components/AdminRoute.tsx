import { Navigate, Outlet, useOutletContext } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function AdminRoute() {
  const { isAdmin, loading } = useAuth();
  const context = useOutletContext(); // pass AppLayout's context down

  if (loading) return <div className="h-full bg-bg" aria-busy="true" />;
  if (!isAdmin) return <Navigate to="/chat" replace />;
  return <Outlet context={context} />;
}