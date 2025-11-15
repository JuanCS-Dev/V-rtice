import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-primary-500">404</h1>
        <p className="text-xl">Page not found</p>
        <Button onClick={() => navigate("/dashboard")}>Go to Dashboard</Button>
      </div>
    </div>
  );
}
