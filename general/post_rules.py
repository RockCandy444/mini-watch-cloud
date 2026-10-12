def validate_post(title, body):
    """작성과 수정에서 같은 공백 제거 및 필수 입력 규칙을 사용한다."""
    title = title.strip()
    body = body.strip()
    errors = []
    if not title:
        errors.append("제목을 입력해 주세요.")
    if not body:
        errors.append("내용을 입력해 주세요.")
    return title, body, errors
