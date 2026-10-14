"use client";

import { useState } from 'react';
import { request } from '../api/client';

export default function AnalysisClient() {
  const [threshold, setThreshold] = useState('10');
  const [observation, setObservation] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function begin() {
    setBusy(true); setError(''); setReport(null); setObservation(null);
    try {
      const result = await request('/analysis/observation');
      setObservation({ after_id: result.after_id, reference_time: null });
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function load() {
    if (!observation) return;
    if (!/^\d+$/.test(threshold) || Number(threshold) < 1 || Number(threshold) > 100000) {
      setError('비교 기준은 1~100000의 정수로 입력해 주세요.'); return;
    }
    setBusy(true); setError('');
    try {
      const query = new URLSearchParams({ threshold, after_id: String(observation.after_id) });
      if (observation.reference_time) query.set('reference_time', observation.reference_time);
      const result = await request(`/analysis?${query}`);
      setObservation({ after_id: result.after_id, reference_time: result.reference_time });
      setReport(result);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  const card = report?.cards[0];
  return (
    <section className="analysis-panel" aria-labelledby="analysis-title">
      <div className="analysis-heading">
        <div><p className="eyebrow">HTTP OBSERVATION</p><h2 id="analysis-title">실제 요청 분석</h2></div>
        <span className="analysis-window">최근 60초 · DB 수신시각</span>
      </div>
      <p className="muted">새 관찰을 시작한 뒤 일반 게시판에 요청을 보내고, 1분 안에 첫 결과를 불러오세요.</p>
      <div className="analysis-controls">
        <button className="secondary" disabled={busy} onClick={begin}>새 관찰 시작</button>
        <label htmlFor="http-threshold">비교 기준</label>
        <input id="http-threshold" type="number" min="1" max="100000" step="1" value={threshold}
          disabled={busy} onChange={(event) => setThreshold(event.target.value)} />
        <button className="primary" disabled={busy || !observation} onClick={load}>
          {busy ? '처리 중…' : '결과 불러오기'}
        </button>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {observation && <p className="analysis-boundary">시작 ID: {observation.after_id} 이후 · 기준시각: {observation.reference_time || '첫 결과 조회 때 고정'}
        <br />기준만 바꾸면 같은 관찰 구간을 사용합니다. 새 관찰은 기존 기록을 보존합니다.</p>}
      {!observation && !busy && <p className="analysis-empty">새 관찰 시작을 눌러 이번 요청의 기준점을 정하세요.</p>}
      {card && <article className={`analysis-card ${card.matched ? 'candidate' : ''}`} aria-live="polite">
        <div className="analysis-result"><h3>{card.title}</h3><strong className="analysis-verdict">{card.verdict}</strong></div>
        <div className="analysis-metrics">
          <div><span>관찰값</span><strong>{card.observed}<small>회</small></strong></div>
          <div><span>비교 기준</span><strong>{card.threshold}<small>회</small></strong></div>
          <div><span>근거</span><strong>{card.records.length}<small>행</small></strong></div>
        </div>
        <p>{card.reason}</p>
        <p className="muted">{report.limitation}</p>
        <details className="analysis-evidence">
          <summary>근거 보기 ({card.records.length}행)</summary>
          {card.records.length ? <div className="analysis-table-scroll"><table>
            <caption>원본 ID와 DB 수신시각으로 연결한 HTTP 근거</caption>
            <thead><tr><th>ID</th><th>수신시각 (UTC)</th><th>방법</th><th>경로</th><th>상태</th><th>종류</th></tr></thead>
            <tbody>{card.records.map((row) => <tr key={row.id} className={row.status_code === 404 ? 'context-row' : ''}>
              <td>{row.id}</td><td><time dateTime={row.occurred_at}>{row.occurred_at}</time></td>
              <td>{row.method}</td><td>{row.path}</td><td>{row.status_code}</td><td>{row.kind}</td>
            </tr>)}</tbody>
          </table></div> : <p className="analysis-empty">해당 근거 없음</p>}
        </details>
      </article>}
    </section>
  );
}
