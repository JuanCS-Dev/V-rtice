import { Outlet } from "react-router-dom";
import { Header } from "./Header/Header";
import { Sidebar } from "./Sidebar/Sidebar";
import { Footer } from "./Footer/Footer";
import { useUIStore } from "@/stores/uiStore";

export function MainLayout() {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="flex h-screen overflow-hidden bg-[rgb(var(--background))]">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main
          className={`flex-1 overflow-y-auto transition-all duration-200 ${
            sidebarOpen ? "ml-64" : "ml-0"
          }`}
        >
          <div className="min-h-full p-6 pb-0">
            <Outlet />
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}
