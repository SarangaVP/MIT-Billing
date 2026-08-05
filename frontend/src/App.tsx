import "./App.css";
import EmployeesPage from "./pages/EmployeesPage";

export default function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MIT</span>
          <span className="brand-name">Mobile Billing</span>
        </div>
        <nav className="topnav">
          <span className="topnav-item active">Employees</span>
          <span className="topnav-item disabled" title="Coming next">
            Bills
          </span>
          <span className="topnav-item disabled" title="Coming next">
            Allocations
          </span>
        </nav>
      </header>
      <main className="content">
        <EmployeesPage />
      </main>
    </div>
  );
}