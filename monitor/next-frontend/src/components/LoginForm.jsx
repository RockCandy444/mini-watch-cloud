import { useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, ShieldCheck } from "lucide-react";
import { login } from "../api/auth";

export default function LoginForm({ onLogin, initialError, onRetry }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await login(username, password);
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story">
        <div className="brand">
          <Activity size={25} /> mini watch<span>MONITOR</span>
        </div>
        <div className="story-copy">
          <p className="eyebrow">A LITTLE WATCH. A CLEARER VIEW.</p>
          <h1>
            작은 기록에서
            <br />
            서비스의 흐름을 읽다.
          </h1>
          <p>
            요청을 살펴보고, 발견한 것을 기록하세요.
            <br />
            우리 서비스의 오늘을 한눈에.
          </p>
          <div className="signal-art" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>
        <p className="story-footer">GENERAL → MONITOR → INSIGHT</p>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <span className="icon-tile">
            <ShieldCheck />
          </span>
          <p className="eyebrow">OPERATOR ACCESS</p>
          <h2>다시 만나 반가워요</h2>
          <p className="muted">운영자 계정으로 대시보드에 로그인하세요.</p>
          <form onSubmit={submit} noValidate>
            <label>
              아이디
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="운영자 아이디"
              />
            </label>
            <label>
              비밀번호
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="비밀번호 입력"
              />
            </label>
            {(error || initialError) && (
              <p role="alert" className="error">
                {error || initialError}
              </p>
            )}
            <button className="primary login-submit" disabled={busy}>
              {busy ? "확인 중…" : "로그인"}
              <ArrowRight size={18} />
            </button>
          </form>
          {initialError && (
            <button className="text-button" onClick={onRetry}>
              연결 다시 확인
            </button>
          )}
          <p className="login-help">
            계정이 없나요? <Link className="auth-link" href="/register">회원가입</Link>
            <br />일반 게시판 계정은 <Link className="auth-link" href="/register/general">여기서 만들기</Link>
          </p>
        </div>
        <p className="login-footnote">
          mini watch · 서비스 관찰을 위한 작은 작업 공간
        </p>
      </section>
    </main>
  );
}
