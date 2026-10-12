const form = document.getElementById("login-form");
const result = document.getElementById("login-result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  result.hidden = false;
  result.textContent = "확인하고 있습니다…";
  result.className = "login-message";
  try {
    const response = await fetch(form.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: form.elements.username.value, password: form.elements.password.value }),
    });
    const data = await response.json();
    result.textContent = response.ok ? `${data.user.username}님, ${data.message}` : data.error;
    result.className = `login-message ${response.ok ? "success" : "failure"}`;
  } catch {
    result.textContent = "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.";
    result.className = "login-message failure";
  } finally {
    button.disabled = false;
  }
});
