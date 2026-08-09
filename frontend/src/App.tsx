import { useState } from "react";
import EmployeesPage from "./pages/EmployeesPage";
import BillsPage from "./pages/BillsPage";
import SettingsPage from "./pages/SettingsPage";
import MobitelEmployeesPage from "./mobitel/pages/MobitelEmployeesPage";
import MobitelBillsPage from "./mobitel/pages/MobitelBillsPage";
import DialogDataEmployeesPage from "./dialog-data/pages/DialogDataEmployeesPage";
import DialogDataBillsPage from "./dialog-data/pages/DialogDataBillsPage";
import SltTeamPackageBillsPage from "./slt/pages/SltTeamPackageBillsPage";
import SltGeneralBillsPage from "./slt/pages/SltGeneralBillsPage";
import "./App.css";

type Module = "dialog_mobile" | "mobitel_data_bucket" | "dialog_data_bucket" | "slt";
type DialogTab = "employees" | "bills" | "settings";
type MobitelTab = "employees" | "bills";
type DialogDataTab = "employees" | "bills";
type SltTab = "team_package" | "general";

export default function App() {
  const [module, setModule] = useState<Module>("dialog_mobile");
  const [dialogTab, setDialogTab] = useState<DialogTab>("employees");
  const [mobitelTab, setMobitelTab] = useState<MobitelTab>("employees");
  const [dialogDataTab, setDialogDataTab] = useState<DialogDataTab>("employees");
  const [sltTab, setSltTab] = useState<SltTab>("team_package");

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MIT</span>
          <span className="brand-name">Billing</span>
        </div>
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
      </header>

      {module === "dialog_mobile" && (
        <div className="subnav">
          <span className={`subnav-item ${dialogTab === "employees" ? "active" : ""}`} onClick={() => setDialogTab("employees")}>
            Employees
          </span>
          <span className={`subnav-item ${dialogTab === "bills" ? "active" : ""}`} onClick={() => setDialogTab("bills")}>
            Bills
          </span>
          <span className={`subnav-item ${dialogTab === "settings" ? "active" : ""}`} onClick={() => setDialogTab("settings")}>
            Settings
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
        {module === "dialog_mobile" && dialogTab === "settings" && <SettingsPage />}

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