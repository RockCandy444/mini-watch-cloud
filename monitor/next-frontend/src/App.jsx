"use client";

import { useEffect, useState } from "react";
import * as auth from "./api/auth";
import LoginForm from "./components/LoginForm";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setChecking(true);
    setError("");
    auth
      .currentUser()
      .then((data) => {
        if (active) setUser(data.user);
      })
      .catch((err) => {
        if (active && err.status !== 401) setError(err.message);
      })
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);
  useEffect(() => {
    const expire = () => {
      setUser(null);
      setError("로그인이 만료되었습니다. 다시 로그인해 주세요.");
    };
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, []);
  async function onLogout() {
    try {
      await auth.logout();
      setUser(null);
      setError("");
    } catch (err) {
      if (err.status === 401) {
        setUser(null);
        setError("");
      } else throw err;
    }
  }
  if (checking)
    return (
      <div className="loading-page">
        mini watch <span>로그인 상태 확인 중…</span>
      </div>
    );
  return user ? (
    <Dashboard user={user} onLogout={onLogout} />
  ) : (
    <LoginForm
      onLogin={setUser}
      initialError={error}
      onRetry={() => setRetry((value) => value + 1)}
    />
  );
}
