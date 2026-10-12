import { useEffect, useRef, useState } from "react";
import { Plus, RefreshCw, ArrowUpRight, NotebookPen } from "lucide-react";
import * as api from "../api/notes";
import NoteForm from "./NoteForm";
import NoteDetail from "./NoteDetail";
import DeleteConfirm from "./DeleteConfirm";

export default function NotesPanel() {
  const [notes, setNotes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState("detail");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const sequence = useRef(0);
  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.listNotes();
      setNotes(data.notes);
      if (selected && !data.notes.some((n) => n.id === selected.id))
        setSelected(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    return () => {
      sequence.current++;
    };
  }, []);
  async function select(id) {
    const token = ++sequence.current;
    setError("");
    setNotice("");
    setLoading(true);
    try {
      const data = await api.getNote(id);
      if (token === sequence.current) {
        setSelected(data.note);
        setMode("detail");
        setFormError("");
      }
    } catch (err) {
      if (token === sequence.current) setError(err.message);
    } finally {
      if (token === sequence.current) setLoading(false);
    }
  }
  async function refresh() {
    await load();
    if (selected) await select(selected.id);
  }
  async function save(values) {
    setBusy(true);
    setFormError("");
    setNotice("");
    try {
      const data =
        mode === "edit"
          ? await api.updateNote(selected.id, values)
          : await api.createNote(values);
      setSelected(data.note);
      setMode("detail");
      setNotice("메모를 저장했습니다.");
      await load();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    setBusy(true);
    setDeleteError("");
    try {
      await api.deleteNote(selected.id);
      setSelected(null);
      setDeleting(false);
      setMode("detail");
      setNotice("메모를 삭제했습니다.");
      await load();
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">OBSERVATION JOURNAL</p>
          <h1>
            관찰 메모<span className="heading-dot">.</span>
          </h1>
          <p>발견한 내용과 다음 할 일을, 하나의 기록으로.</p>
        </div>
        <div className="heading-actions">
          <button
            className="secondary"
            disabled={busy || loading}
            onClick={refresh}
          >
            <RefreshCw size={16} />
            메모 새로고침
          </button>
          <button
            className="primary"
            disabled={busy || loading}
            onClick={() => {
              sequence.current++;
              setMode("new");
              setFormError("");
              setNotice("");
            }}
          >
            <Plus size={17} />새 메모
          </button>
        </div>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      <div className="notes-layout">
        <section className="panel notes-list">
          <div className="panel-title">
            <div>
              <h2>모든 메모</h2>
              <span className="count-badge">{notes.length}</span>
            </div>
            <NotebookPen size={18} />
          </div>
          {loading && <p className="list-loading">메모를 불러오고 있습니다…</p>}
          {notes.map((note) => (
            <button
              key={note.id}
              className={`note-item ${selected?.id === note.id ? "selected" : ""}`}
              disabled={busy || loading || mode !== "detail"}
              onClick={() => select(note.id)}
            >
              <span className="note-item-meta">
                #{note.id}
                <span className={`status-tag status-${note.status}`}>
                  {note.status}
                </span>
              </span>
              <strong>{note.title}</strong>
              <span className="note-item-foot">
                {new Date(note.updated_at).toLocaleDateString("ko-KR")}
                <ArrowUpRight size={16} />
              </span>
            </button>
          ))}
          {!notes.length && !loading && !error && (
            <div className="empty">
              <NotebookPen size={27} />
              <h3>아직 메모가 없습니다</h3>
              <p>첫 관찰을 기록해 보세요.</p>
            </div>
          )}
        </section>
        <section className="panel note-content">
          {mode === "detail" ? (
            <NoteDetail
              note={selected}
              busy={busy || loading}
              onEdit={() => {
                setMode("edit");
                setFormError("");
                setNotice("");
              }}
              onDelete={() => {
                setDeleting(true);
                setDeleteError("");
              }}
            />
          ) : (
            <NoteForm
              key={`${mode}-${selected?.id || "new"}`}
              note={mode === "edit" ? selected : null}
              busy={busy}
              error={formError}
              onSave={save}
              onCancel={() => {
                setMode("detail");
                setFormError("");
              }}
            />
          )}
        </section>
      </div>
      {deleting && (
        <DeleteConfirm
          note={selected}
          busy={busy}
          error={deleteError}
          onCancel={() => setDeleting(false)}
          onConfirm={remove}
        />
      )}
    </>
  );
}
