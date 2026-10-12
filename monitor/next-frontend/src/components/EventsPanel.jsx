import { useEffect, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Search,
  ArrowDown,
  Filter,
} from "lucide-react";
import { listEvents } from "../api/events";

export default function EventsPanel() {
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState({ total: 0, errors: 0 });
  const [path, setPath] = useState("");
  const [status, setStatus] = useState("");
  const [filters, setFilters] = useState({});
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [updated, setUpdated] = useState(null);
  const sequence = useRef(0);
  async function load(next = filters) {
    const id = ++sequence.current;
    setBusy(true);
    setError("");
    try {
      const data = await listEvents(next);
      if (id === sequence.current) {
        setEvents(data.events);
        setSummary(data.summary);
        setUpdated(new Date());
      }
    } catch (err) {
      if (id === sequence.current) setError(err.message);
    } finally {
      if (id === sequence.current) setBusy(false);
    }
  }
  useEffect(() => {
    load({});
    return () => {
      sequence.current++;
    };
  }, []);
  function search(e) {
    e.preventDefault();
    const next = { path: path.trim(), status };
    setFilters(next);
    load(next);
  }
  function clear() {
    setPath("");
    setStatus("");
    setFilters({});
    load({});
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">SERVICE OBSERVABILITY</p>
          <h1>
            요청 기록<span className="heading-dot">.</span>
          </h1>
          <p>서비스가 남긴 흔적을 살펴보고, 중요한 순간을 발견하세요.</p>
        </div>
        <button className="secondary" onClick={() => load()} disabled={busy}>
          <RefreshCw size={16} className={busy ? "spin" : ""} />
          {busy ? "조회 중…" : "기록 새로고침"}
        </button>
      </div>
      <div className="stat-grid">
        <Stat
          icon={<Activity />}
          label="전체 요청"
          value={summary.total}
          tone="purple"
          note="현재 조회 조건의 모든 기록"
        />
        <Stat
          icon={<AlertCircle />}
          label="오류 요청"
          value={summary.errors}
          tone="orange"
          note="응답 상태 코드 400 이상"
        />
        <Stat
          icon={<CheckCircle2 />}
          label="오류 외 요청"
          value={summary.total - summary.errors}
          tone="green"
          note="응답 상태 코드 400 미만"
        />
      </div>
      <section className="panel events-panel">
        <div className="panel-title">
          <div>
            <span className="live-dot" />
            <h2>요청 타임라인</h2>
            <span className="count-badge">{events.length}</span>
          </div>
          <span className="updated">
            {updated
              ? `${updated.toLocaleTimeString("ko-KR")} 조회`
              : "첫 조회 대기 중"}
          </span>
        </div>
        <form className="filter-bar" onSubmit={search}>
          <div className="search-field">
            <Search size={17} />
            <input
              aria-label="요청 경로 검색"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="경로로 검색 · 예: /board"
            />
          </div>
          <select
            aria-label="응답 상태 코드"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">모든 상태 코드</option>
            <option value="errors">오류 전체 (400 이상)</option>
            {[200, 201, 303, 400, 401, 403, 404, 500].map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
          <button className="secondary" disabled={busy}>
            <Filter size={15} />
            조회
          </button>
          <button
            className="text-button"
            type="button"
            onClick={clear}
            disabled={busy}
          >
            조건 해제
          </button>
        </form>
        {error && (
          <p className="error panel-error" role="alert">
            {error}
          </p>
        )}
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>
                  요청 시각 <ArrowDown size={12} />
                </th>
                <th>메서드</th>
                <th>요청 경로</th>
                <th>기록 종류</th>
                <th>응답 상태</th>
                <th>기록 번호</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td className="time-cell">
                    {new Date(event.occurred_at).toLocaleString("ko-KR")}
                  </td>
                  <td>
                    <span
                      className={`method method-${event.method.toLowerCase()}`}
                    >
                      {event.method}
                    </span>
                  </td>
                  <td className="path-cell">{event.path}</td>
                  <td>{event.event_type}</td>
                  <td>
                    <span
                      className={
                        event.status_code >= 400
                          ? "response-code failure"
                          : "response-code success"
                      }
                    >
                      <i />
                      {event.status_code}
                    </span>
                  </td>
                  <td className="id-cell">#{event.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!events.length && !busy && !error && (
          <div className="empty">
            <RadioIcon />
            <h3>
              {filters.path || filters.status
                ? "조건에 맞는 기록이 없습니다"
                : "아직 수집된 요청이 없습니다"}
            </h3>
            <p>
              {filters.path || filters.status
                ? "검색 조건을 해제해 전체 기록을 살펴보세요."
                : "일반 게시판에 접속한 후 기록을 새로고침하세요."}
            </p>
          </div>
        )}
        {busy && !events.length && (
          <div className="empty">요청 기록을 불러오고 있습니다…</div>
        )}
        <div className="table-footer">
          <span>최신 기록부터 표시 · 현재 조회한 전체 기록 기준 집계</span>
          <span>오류 기준: HTTP ≥ 400</span>
        </div>
      </section>
      <div className="hint">
        <NotebookIcon />
        <p>
          <strong>기록에서 발견한 내용을 남겨보세요.</strong> 관찰 메모에서
          발견한 문제와 처리 상태를 함께 관리할 수 있어요.
        </p>
      </div>
    </>
  );
}
function Stat({ icon, label, value, tone, note }) {
  return (
    <section className={`stat-card ${tone}`}>
      <div>
        <span className="stat-label">{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong>
        {value.toLocaleString()}
        <small>건</small>
      </strong>
      <p>{note}</p>
    </section>
  );
}
function RadioIcon() {
  return <Activity size={28} />;
}
function NotebookIcon() {
  return <CheckCircle2 size={19} />;
}
