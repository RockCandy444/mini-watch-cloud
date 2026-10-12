import { useEffect, useRef } from "react";
import { Trash2 } from "lucide-react";
export default function DeleteConfirm({
  note,
  onCancel,
  onConfirm,
  busy,
  error,
}) {
  const dialog = useRef(null);
  useEffect(() => {
    dialog.current.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="delete-dialog"
      aria-labelledby="delete-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
    >
      <span className="delete-icon">
        <Trash2 />
      </span>
      <h2 id="delete-title">메모를 삭제할까요?</h2>
      <p>
        <strong>{note.title}</strong>
      </p>
      <p className="muted">확정하면 이 관찰 메모가 삭제됩니다.</p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="form-actions">
        <button
          autoFocus
          className="secondary"
          disabled={busy}
          onClick={onCancel}
        >
          취소
        </button>
        <button className="danger" disabled={busy} onClick={onConfirm}>
          {busy ? "삭제 중…" : "삭제 확인"}
        </button>
      </div>
    </dialog>
  );
}
