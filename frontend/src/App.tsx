import { useEffect, useState } from "react";
import EmployeesPage from "./pages/EmployeesPage";
import BillsPage from "./pages/BillsPage";
import MobitelEmployeesPage from "./mobitel/pages/MobitelEmployeesPage";
import MobitelBillsPage from "./mobitel/pages/MobitelBillsPage";
import DialogDataEmployeesPage from "./dialog-data/pages/DialogDataEmployeesPage";
import DialogDataBillsPage from "./dialog-data/pages/DialogDataBillsPage";
import SltTeamPackageBillsPage from "./slt/pages/SltTeamPackageBillsPage";
import SltGeneralBillsPage from "./slt/pages/SltGeneralBillsPage";
import "./App.css";

type Module = "dialog_mobile" | "mobitel_data_bucket" | "dialog_data_bucket" | "slt";
type DialogTab = "employees" | "bills";
type MobitelTab = "employees" | "bills";
type DialogDataTab = "employees" | "bills";
type SltTab = "team_package" | "general";
type Theme = "dark" | "light";

const THEME_STORAGE_KEY = "mit-billing-theme";

function getInitialTheme(): Theme {
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "light" ? "light" : "dark";
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
    </svg>
  );
}

export default function App() {
  const [module, setModule] = useState<Module>("dialog_mobile");
  const [dialogTab, setDialogTab] = useState<DialogTab>("employees");
  const [mobitelTab, setMobitelTab] = useState<MobitelTab>("employees");
  const [dialogDataTab, setDialogDataTab] = useState<DialogDataTab>("employees");
  const [sltTab, setSltTab] = useState<SltTab>("team_package");
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MIT</span>
          <span className="brand-name">Billing</span>
        </div>
        <div className="topbar-right">
          <nav className="topnav">
            <span
              className={`topnav-item ${module === "dialog_mobile" ? "active" : ""}`}
              onClick={() => setModule("dialog_mobile")}
            >
              Dialog Mobile
            </span>
            <span
              className={`topnav-item ${module === "mobitel_data_bucket" ? "active" : ""}`}
              onClick={() => setModule("mobitel_data_bucket")}
            >
              Mobitel Data Bucket
            </span>
            <span
              className={`topnav-item ${module === "dialog_data_bucket" ? "active" : ""}`}
              onClick={() => setModule("dialog_data_bucket")}
            >
              Dialog Data Bucket
            </span>
            <span
              className={`topnav-item ${module === "slt" ? "active" : ""}`}
              onClick={() => setModule("slt")}
            >
              SLT
            </span>
          </nav>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </header>

      {module === "dialog_mobile" && (
        <div className="subnav">
          <span className={`subnav-item ${dialogTab === "employees" ? "active" : ""}`} onClick={() => setDialogTab("employees")}>
            Employees
          </span>
          <span className={`subnav-item ${dialogTab === "bills" ? "active" : ""}`} onClick={() => setDialogTab("bills")}>
            Bills
          </span>
        </div>
      )}

      {module === "mobitel_data_bucket" && (
        <div className="subnav">
          <span className={`subnav-item ${mobitelTab === "employees" ? "active" : ""}`} onClick={() => setMobitelTab("employees")}>
            Employees
          </span>
          <span className={`subnav-item ${mobitelTab === "bills" ? "active" : ""}`} onClick={() => setMobitelTab("bills")}>
            Bills
          </span>
        </div>
      )}

      {module === "dialog_data_bucket" && (
        <div className="subnav">
          <span className={`subnav-item ${dialogDataTab === "employees" ? "active" : ""}`} onClick={() => setDialogDataTab("employees")}>
            Employees
          </span>
          <span className={`subnav-item ${dialogDataTab === "bills" ? "active" : ""}`} onClick={() => setDialogDataTab("bills")}>
            Bills
          </span>
        </div>
      )}

      {module === "slt" && (
        <div className="subnav">
          <span className={`subnav-item ${sltTab === "team_package" ? "active" : ""}`} onClick={() => setSltTab("team_package")}>
            Team Package
          </span>
          <span className={`subnav-item ${sltTab === "general" ? "active" : ""}`} onClick={() => setSltTab("general")}>
            General Bills
          </span>
        </div>
      )}

      <main className="content">
        {module === "dialog_mobile" && dialogTab === "employees" && <EmployeesPage />}
        {module === "dialog_mobile" && dialogTab === "bills" && <BillsPage />}

        {module === "mobitel_data_bucket" && mobitelTab === "employees" && <MobitelEmployeesPage />}
        {module === "mobitel_data_bucket" && mobitelTab === "bills" && <MobitelBillsPage />}

        {module === "dialog_data_bucket" && dialogDataTab === "employees" && <DialogDataEmployeesPage />}
        {module === "dialog_data_bucket" && dialogDataTab === "bills" && <DialogDataBillsPage />}

        {module === "slt" && sltTab === "team_package" && <SltTeamPackageBillsPage />}
        {module === "slt" && sltTab === "general" && <SltGeneralBillsPage />}
      </main>
    </div>
  );
}