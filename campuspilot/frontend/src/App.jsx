import { useState } from "react";
import Icon from "./components/common/Icon";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Planner from "./pages/Planner";
import CourseDetail from "./pages/CourseDetail";
import Quiz from "./pages/Quiz";
import Progress from "./pages/Progress";
import PlanReview from "./pages/PlanReview";
import History from "./pages/History";

const TABS = [
  { name: "Dashboard", icon: "home", Page: Dashboard },
  { name: "Chat", icon: "chat", Page: Chat },
  { name: "Planner", icon: "calendar", Page: Planner },
  { name: "Courses", icon: "book", Page: CourseDetail },
  { name: "Quiz", icon: "quiz", Page: Quiz },
  { name: "Progress", icon: "chart", Page: Progress },
  { name: "Recovery Agent", icon: "zap", Page: PlanReview },
  { name: "History", icon: "history", Page: History },
];

export default function App() {
  const [tab, setTab] = useState("Dashboard");
  const { Page } = TABS.find((t) => t.name === tab);

  return (
    <>
      <div className="bg">
        <div className="blob b1" />
        <div className="blob b2" />
        <div className="blob b3" />
      </div>

      <div className="layout">
        <aside className="sidebar">
          <div className="logo">
            <span className="logo-mark"><Icon name="sparkle" size={20} /></span>
            CampusPilot
          </div>

          {TABS.map((t) => (
            <button key={t.name} className={`nav-item ${tab === t.name ? "active" : ""}`}
                    onClick={() => setTab(t.name)}>
              <Icon name={t.icon} />
              {t.name}
            </button>
          ))}

          <div className="sidebar-foot">Your adaptive academic recovery agent</div>
        </aside>

        <main className="main">
          {/* key reloads the page data every time you switch tabs */}
          <div className="page" key={tab}>
            <Page />
          </div>
        </main>
      </div>
    </>
  );
}