import { Pencil, Trash2, FileText } from "lucide-react";
export default function NoteDetail({ note, onEdit, onDelete, busy }) {
  if (!note)
    return (
      <div className="empty detail-empty">
        <FileText size={32} />
        <h3>관찰을 기록으로 남기세요</h3>
        <p>목록에서 메모를 선택하거나 새 메모를 작성하세요.</p>
      </div>
    );
  return (
    <article className="note-detail">
      <div className="detail-meta">
        <span>OBSERVATION / #{note.id}</span>
        <span className={`status-tag status-${note.status}`}>
          {note.status}
        </span>
      </div>
      <h2>{note.title}</h2>
      <p className="updated">
        마지막 수정 · {new Date(note.updated_at).toLocaleString("ko-KR")}
      </p>
      <div className="note-body">{note.body}</div>
      <div className="form-actions">
        <button className="secondary" disabled={busy} onClick={onEdit}>
          <Pencil size={15} />
          수정
        </button>
        <button className="danger-text" disabled={busy} onClick={onDelete}>
          <Trash2 size={15} />
          삭제
        </button>
      </div>
    </article>
  );
}
