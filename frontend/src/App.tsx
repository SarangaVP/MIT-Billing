import { useState } from "react";
import EmployeesPage from "./pages/EmployeesPage";
import BillsPage from "./pages/BillsPage";
import SettingsPage from "./pages/SettingsPage";
import "./App.css";

type Tab = "employees" | "bills" | "settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("employees");

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MIT</span>
          <span className="brand-name">Mobile Billing</span>
        </div>
        <nav className="topnav">
          <span className={`topnav-item ${tab === "employees" ? "active" : ""}`} onClick={() => setTab("employees")}>
            Employees
          </span>
          <span className={`topnav-item ${tab === "bills" ? "active" : ""}`} onClick={() => setTab("bills")}>
            Bills
          </span>
          <span className="topnav-item disabled" title="Coming next">
            Allocations
          </span>
          <span className={`topnav-item ${tab === "settings" ? "active" : ""}`} onClick={() => setTab("settings")}>
            Settings
          </span>
        </nav>
      </header>
      <main className="content">
        {tab === "employees" && <EmployeesPage />}
        {tab === "bills" && <BillsPage />}
        {tab === "settings" && <SettingsPage />}
      </main>
    </div>
  );
}