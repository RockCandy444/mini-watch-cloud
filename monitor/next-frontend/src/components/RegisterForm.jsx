"use client";

import { useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, UserPlus, CheckCircle2 } from "lucide-react";
import { register } from "../api/auth";

export default function RegisterForm({ accountType }) {
  const general = accountType === "general";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [created, setCreated] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setError("");
    if (!/^[A-Za-z0-9_-]{3,30}$/.test(username.trim())) {
      setError("아이디는 영문, 숫자, 밑줄, 하이픈으로 3~30자 입력해 주세요.");
      return;
    }
    if (password.length < 8 || password.length > 128 || !password.trim()) {
      setError("비밀번호는 공백만 사용하지 않고 8~128자로 입력해 주세요.");
      return;
    }
    if (password !== confirm) {
      setError("비밀번호 확인이 일치하지 않습니다.");
      return;
    }
    setBusy(true);
    try {
      const data = await register(accountType, username.trim(), password, confirm);
      setCreated(data.user);
      setPassword("");
      setConfirm("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page register-page">
      <section className="login-story">
        <Link href="/" className="brand"><Activity size={25} /> mini watch<span>YOUR FIRST STEP</span></Link>
        <div className="story-copy">
          <p className="eyebrow">A NEW ACCOUNT. A FRESH START.</p>
          <h1>계정 하나로,<br />바로 시작하세요.</h1>
          <p>아이디를 정하고 비밀번호를 입력하면 준비 끝.<br />{general ? "게시판에서 로그인 결과를 확인해 보세요." : "서비스 기록과 관찰 메모를 만나 보세요."}</p>
          <div className="signal-art" aria-hidden="true">{Array.from({ length: 12 }, (_, i) => <i key={i} />)}</div>
        </div>
        <p className="story-footer">GENERAL → MONITOR → INSIGHT</p>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <span className="icon-tile">{created ? <CheckCircle2 /> : <UserPlus />}</span>
          <p className="eyebrow">{general ? "GENERAL ACCOUNT" : "MONITOR ACCOUNT"}</p>
          <h2>{created ? "가입이 완료됐어요" : "처음 오셨나요?"}</h2>
          {created ? (
            <div className="registration-success">
              <p role="status" className="notice"><strong>{created.username}</strong> 계정이 만들어졌습니다.<br />입력한 비밀번호로 로그인해 주세요.</p>
              {general ? <a className="primary login-submit" href="http://localhost:8081/login">게시판 로그인으로 이동 <ArrowRight size={18} /></a> : <Link className="primary login-submit" href="/">대시보드 로그인으로 이동 <ArrowRight size={18} /></Link>}
              <button className="text-button" onClick={() => { setCreated(null); setUsername(""); setError(""); }}>다른 계정 만들기</button>
            </div>
          ) : (
            <>
              <p className="muted">{general ? "일반 게시판" : "감시 대시보드"}에서 사용할 계정을 만드세요.</p>
              <nav className="account-tabs" aria-label="만들 계정 종류">
                <Link href="/register" aria-current={!general ? "page" : undefined} className={!general ? "active" : ""}>대시보드 계정</Link>
                <Link href="/register/general" aria-current={general ? "page" : undefined} className={general ? "active" : ""}>게시판 계정</Link>
              </nav>
              <form onSubmit={submit} noValidate>
                <fieldset disabled={busy}>
                  <label>아이디<input name="username" autoComplete="username" maxLength={30} value={username} onChange={(e) => setUsername(e.target.value)} placeholder="예: student01" aria-describedby="username-help" /></label>
                  <p className="field-hint" id="username-help">영문, 숫자, 밑줄, 하이픈 · 3~30자</p>
                  <label>비밀번호<input name="password" type="password" autoComplete="new-password" maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="8자 이상 입력" /></label>
                  <label>비밀번호 확인<input name="password_confirm" type="password" autoComplete="new-password" maxLength={128} value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="같은 비밀번호를 한 번 더 입력" /></label>
                  {error && <p role="alert" className="error">{error}</p>}
                  <button className="primary login-submit" type="submit" disabled={busy}>{busy ? "계정 만드는 중…" : "회원가입"}<ArrowRight size={18} /></button>
                </fieldset>
              </form>
              <p className="login-help">이미 계정이 있나요? {general ? <a className="auth-link" href="http://127.0.0.1:5100/login">게시판 로그인</a> : <Link className="auth-link" href="/">로그인</Link>}</p>
            </>
          )}
        </div>
        <p className="login-footnote">mini watch · 서비스 관찰을 위한 작은 작업 공간</p>
      </section>
    </main>
  );
}
