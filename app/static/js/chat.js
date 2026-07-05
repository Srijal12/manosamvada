/**
 * Manosamvada — Chat Interface Controller
 * Handles message sending, streaming-style typing indicator,
 * session switching, and sidebar interactions.
 */

(function () {
  "use strict";

  const messagesEl = document.getElementById("chat-messages");
  const formEl = document.getElementById("chat-input-form");
  const textareaEl = document.getElementById("chat-textarea");
  const sessionListEl = document.getElementById("session-list");
  const newSessionBtn = document.getElementById("new-session-btn");
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebarEl = document.getElementById("chat-sidebar");

  let currentSessionId = messagesEl ? messagesEl.dataset.sessionId || null : null;

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderMessage(role, content, emotion, isCrisis) {
    const row = document.createElement("div");
    row.className = "msg-row " + role + (isCrisis ? " crisis" : "");

    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = role === "assistant" ? "◐" : "you";

    const bubbleWrap = document.createElement("div");

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");

    bubbleWrap.appendChild(bubble);

    if (role === "user" && emotion) {
      const tag = document.createElement("span");
      tag.className = "emotion-tag";
      tag.textContent = "felt: " + emotion;
      bubbleWrap.appendChild(tag);
    }

    row.appendChild(avatar);
    row.appendChild(bubbleWrap);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function renderTypingIndicator() {
    const row = document.createElement("div");
    row.className = "msg-row assistant";
    row.id = "typing-row";

    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = "◐";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerHTML =
      '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const row = document.getElementById("typing-row");
    if (row) row.remove();
  }

  async function sendMessage(text) {
    renderMessage("user", text, null, false);
    renderTypingIndicator();

    try {
      const res = await fetch("/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: currentSessionId,
        }),
      });

      const data = await res.json();
      removeTypingIndicator();

      if (!res.ok) {
        renderMessage("assistant", data.error || "Something went wrong. Please try again.", null, false);
        return;
      }

      currentSessionId = data.session_id || currentSessionId;
      renderMessage("assistant", data.response, null, data.is_crisis);

      // Update the emotion tag on the just-sent user message
      const userRows = messagesEl.querySelectorAll(".msg-row.user");
      const lastUserRow = userRows[userRows.length - 1];
      if (lastUserRow && data.emotion) {
        const tag = document.createElement("span");
        tag.className = "emotion-tag";
        tag.textContent = "felt: " + data.emotion;
        lastUserRow.querySelector("div:last-child").appendChild(tag);
      }
    } catch (err) {
      removeTypingIndicator();
      renderMessage(
        "assistant",
        "I'm having trouble connecting right now. Please check your connection and try again.",
        null,
        false
      );
      console.error("Chat send error:", err);
    }
  }

  if (formEl) {
    formEl.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = textareaEl.value.trim();
      if (!text) return;
      textareaEl.value = "";
      textareaEl.style.height = "auto";
      sendMessage(text);
    });

    textareaEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        formEl.requestSubmit();
      }
    });

    textareaEl.addEventListener("input", () => {
      textareaEl.style.height = "auto";
      textareaEl.style.height = Math.min(textareaEl.scrollHeight, 140) + "px";
    });
  }

  if (newSessionBtn) {
    newSessionBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/chat/new-session", { method: "POST" });
        const data = await res.json();
        if (data.session_id) {
          window.location.reload();
        }
      } catch (err) {
        console.error("New session error:", err);
      }
    });
  }

  if (sessionListEl) {
    sessionListEl.addEventListener("click", async (e) => {
      const item = e.target.closest(".session-item");
      if (!item) return;
      const sessionId = item.dataset.sessionId;

      document.querySelectorAll(".session-item").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");

      try {
        const res = await fetch(`/chat/history/${sessionId}`);
        const data = await res.json();
        if (!res.ok) return;

        currentSessionId = sessionId;
        messagesEl.innerHTML = "";
        data.messages.forEach((m) => {
          renderMessage(m.role, m.content, m.emotion, false);
        });
      } catch (err) {
        console.error("Load history error:", err);
      }
    });
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      sidebarEl.classList.toggle("open");
    });
  }

  scrollToBottom();
})();
