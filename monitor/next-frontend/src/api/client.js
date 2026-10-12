export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export async function request(path, options = {}, basePath = "/api") {
  let response;
  try {
    response = await fetch(`${basePath}${path}`, {
      credentials: "same-origin",
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new ApiError(
      "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
      0,
    );
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      "서버 응답을 읽지 못했습니다. 감시 서버 실행 상태를 확인해 주세요.",
      response.status,
    );
  }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/"))
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      data.error || "요청을 처리하지 못했습니다.",
      response.status,
    );
  }
  return data;
}
