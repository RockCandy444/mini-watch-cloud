import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  Radio,
  NotebookPen,
  ArrowUpRight,
  LogOut,
} from "lucide-react";
import EventsPanel from "./EventsPanel";
import NotesPanel from "./NotesPanel";

export default function Dashboard({ user, onLogout }) {
  const tab = usePathname() === "/notes" ? "notes" : "events";
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function leave() {
    setBusy(true);
    try {
      await onLogout();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity size={25} /> mini watch<span>MONITOR</span>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="대시보드 메뉴">
          <div className="nav-overview">
            <LayoutDashboard size={18} /> 운영 대시보드
          </div>
          <Link
            href="/"
            aria-current={tab === "events" ? "page" : undefined}
            className={tab === "events" ? "nav-item active" : "nav-item"}
          >
            <Radio size={18} /> 요청 기록 <span className="nav-dot" />
          </Link>
          <Link
            href="/notes"
            aria-current={tab === "notes" ? "page" : undefined}
            className={tab === "notes" ? "nav-item active" : "nav-item"}
          >
            <NotebookPen size={18} /> 관찰 메모
          </Link>
        </nav>
        <div className="sidebar-bottom">
          <div className="service-card">
            <span className="live-dot" />
            <div>
              일반 서비스<p>게시판을 열어 요청을 관찰하세요.</p>
            </div>
            <a
              href="http://localhost:8081"
              target="_blank"
              rel="noreferrer"
              aria-label="일반 게시판 열기"
            >
              <ArrowUpRight size={18} />
            </a>
          </div>
          <p>MINI WATCH / NEXT.JS NOTES</p>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            워크스페이스 <span className="slash">/</span>{" "}
            <strong>{tab === "events" ? "요청 기록" : "관찰 메모"}</strong>
          </span>
          <div className="user-menu">
            <span className="avatar">
              {user.username.slice(0, 1).toUpperCase()}
            </span>
            <span>
              {user.username}
              <small>운영자</small>
            </span>
            <button
              className="icon-button"
              aria-label="로그아웃"
              title="로그아웃"
              disabled={busy}
              onClick={leave}
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <main className="workspace">
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          {tab === "events" ? <EventsPanel /> : <NotesPanel />}
        </main>
        <footer className="workspace-footer">
          작은 기록, 더 나은 관찰.<span>mini watch © 2026</span>
        </footer>
      </div>
    </div>
  );
}
