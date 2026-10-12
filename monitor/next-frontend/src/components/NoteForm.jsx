import { useState } from "react";
export default function NoteForm({ note, onSave, onCancel, busy, error }) {
  const [title, setTitle] = useState(note?.title || "");
  const [body, setBody] = useState(note?.body || "");
  const [status, setStatus] = useState(note?.status || "확인 전");
  return (
    <form
      className="note-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSave({ title, body, status });
      }}
      noValidate
    >
      <p className="eyebrow">
        {note ? `EDIT NOTE / #${note.id}` : "NEW OBSERVATION"}
      </p>
      <h2>{note ? "메모 수정" : "새 관찰 메모"}</h2>
      <label htmlFor="db-note-title">
        제목
      </label>
        <input
          id="db-note-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="무엇을 발견했나요?"
        />
      <label htmlFor="db-note-status">
        처리 상태
      </label>
        <select id="db-note-status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option>확인 전</option>
          <option>확인 중</option>
          <option>완료</option>
        </select>
      <label htmlFor="db-note-body">
        내용
      </label>
        <textarea
          id="db-note-body"
          rows={8}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="요청 경로, 응답 상태, 확인한 내용을 자유롭게 기록하세요."
        />
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="form-actions">
        <button
          type="button"
          className="secondary"
          onClick={onCancel}
          disabled={busy}
        >
          취소
        </button>
        <button className="primary" disabled={busy}>
          {busy ? "저장 중…" : "메모 저장"}
        </button>
      </div>
    </form>
  );
}
