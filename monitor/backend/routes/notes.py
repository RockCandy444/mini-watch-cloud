from flask import Blueprint, request
from monitor.backend.repositories import notes
from monitor.backend.routes.auth import require_login

notes_bp = Blueprint('monitor_notes', __name__, url_prefix='/api/notes')
STATUSES = {'확인 전', '확인 중', '완료'}


def validate_note(data):
    if not isinstance(data, dict):
        return None
    title, body, status = data.get('title'), data.get('body'), data.get('status', '확인 전')
    if not isinstance(title, str) or not isinstance(body, str) or not isinstance(status, str):
        return None
    title, body = title.strip(), body.strip()
    if not title or not body or status not in STATUSES:
        return None
    return title, body, status


@notes_bp.get('')
@require_login
def index():
    return {'notes': notes.list_notes()}


@notes_bp.get('/<int:note_id>')
@require_login
def detail(note_id):
    note = notes.find_note(note_id)
    return ({'note': note}, 200) if note else ({'error': '메모를 찾을 수 없습니다.'}, 404)


@notes_bp.post('')
@require_login
def create():
    values = validate_note(request.get_json(silent=True))
    if values is None:
        return {'error': '제목과 내용을 입력하고 올바른 처리 상태를 선택해 주세요.'}, 400
    return {'note': notes.create_note(*values)}, 201


@notes_bp.put('/<int:note_id>')
@require_login
def update(note_id):
    if notes.find_note(note_id) is None:
        return {'error': '메모를 찾을 수 없습니다.'}, 404
    values = validate_note(request.get_json(silent=True))
    if values is None:
        return {'error': '제목과 내용을 입력하고 올바른 처리 상태를 선택해 주세요.'}, 400
    note = notes.update_note(note_id, *values)
    return ({'note': note}, 200) if note else ({'error': '메모를 찾을 수 없습니다.'}, 404)


@notes_bp.delete('/<int:note_id>')
@require_login
def delete(note_id):
    deleted = notes.delete_note(note_id)
    return ({'message': '메모를 삭제했습니다.'}, 200) if deleted else ({'error': '메모를 찾을 수 없습니다.'}, 404)
