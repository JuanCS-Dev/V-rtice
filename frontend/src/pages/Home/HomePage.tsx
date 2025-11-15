import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui";
import { useAuth } from "@/lib/auth/AuthContext";

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-[rgb(var(--background))]">
      <div className="max-w-md space-y-6 text-center">
        <div className="mx-auto h-16 w-16 rounded-full bg-primary-500" />
        <h1 className="text-4xl font-bold text-[rgb(var(--text-primary))]">
          Vértice v3.3.1
        </h1>
        <p className="text-lg text-[rgb(var(--text-secondary))]">
          Clean, Calm, Focused - Cybersecurity Platform
        </p>
        <Button
          size="lg"
          onClick={() => navigate(isAuthenticated ? "/dashboard" : "/login")}
        >
          {isAuthenticated ? "Go to Dashboard" : "Get Started"}
        </Button>
      </div>
    </div>
  );
}
