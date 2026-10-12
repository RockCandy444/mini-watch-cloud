import { request } from "./client";
export const listNotes = () => request("/notes");
export const getNote = (id) => request(`/notes/${id}`);
export const createNote = (note) =>
  request("/notes", { method: "POST", body: JSON.stringify(note) });
export const updateNote = (id, note) =>
  request(`/notes/${id}`, { method: "PUT", body: JSON.stringify(note) });
export const deleteNote = (id) => request(`/notes/${id}`, { method: "DELETE" });
