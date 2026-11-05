"use strict";

const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-chat");
const typing = document.querySelector("#typing");
const notice = document.querySelector("#notice");
const charCount = document.querySelector("#char-count");
let unlocked = false;

function appendMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "message-user" : "message-her"}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "我" : "予";
  const body = document.createElement("div");
  body.className = "message-content";
  const speaker = document.createElement("span");
  speaker.className = "speaker";
  speaker.textContent = role === "user" ? "你" : "周予晴 · 归档回复";
  const text = document.createElement("p");
  text.textContent = content;
  body.append(speaker, text);
  article.append(avatar, body);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(busy) {
  sendButton.disabled = busy;
  input.disabled = busy;
  typing.hidden = !busy;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 116)}px`;
  charCount.textContent = `${input.value.length} / ${input.maxLength}`;
}

async function refreshState() {
  try {
    const response = await fetch("/api/state", { credentials: "same-origin" });
    const state = await response.json();
    unlocked = Boolean(state.unlocked);
  } catch {
    notice.textContent = "留言站暂时无法连接。";
  }
}

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;
  notice.textContent = "";
  appendMessage("user", message);
  input.value = "";
  resizeInput();
  setBusy(true);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "发送失败");
    unlocked = Boolean(result.unlocked);
    appendMessage("assistant", result.reply || "……");
  } catch (error) {
    notice.textContent = error.message || "发送失败，请稍后再试。";
  } finally {
    setBusy(false);
    input.focus();
  }
});

clearButton.addEventListener("click", async () => {
  messages.replaceChildren();
  appendMessage("assistant", "你好。旧留言我还留着一些。想聊什么？");
  notice.textContent = "本地显示已清空；如需重置解锁状态，请清除此站点的会话 Cookie。";
  await refreshState();
});

refreshState();
resizeInput();
