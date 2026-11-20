async function act(url, body) {
  const res = await fetch(url, { method: "POST", body });
  if (res.ok) location.reload();
  else alert((await res.json()).error || "Failed");
}

function updateStage(appId, stage) {
  const body = new URLSearchParams({ stage });
  act(`/applications/${appId}/stage`, body);
}

function snoozeAction(actionId, days = 1) {
  const body = new URLSearchParams({ days: String(days) });
  act(`/actions/${actionId}/snooze`, body);
}

function completeAction(actionId) {
  act(`/actions/${actionId}/complete`);
}

function submitTaskForm(event) {
  event.preventDefault();
  const body = new URLSearchParams(new FormData(event.target));
  act("/tasks", body);
}

/* Mobile & Tablet Navigation Drawer */
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!sidebar) return;
  const opening = !sidebar.classList.contains("open");
  sidebar.classList.toggle("open", opening);
  if (backdrop) backdrop.classList.toggle("open", opening);
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) sidebar.classList.remove("open");
  if (backdrop) backdrop.classList.remove("open");
}

/* Theme toggle & persistence */
function syncThemeButton() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = isDark ? "☀ Light Mode" : "☾ Dark Mode";
  const miniBtn = document.querySelector(".theme-toggle-mini");
  if (miniBtn) miniBtn.textContent = isDark ? "☀" : "☾";
}

function toggleTheme() {
  const root = document.documentElement;
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  if (next === "dark") root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");
  localStorage.setItem("fortehire-theme", next);
  syncThemeButton();
  window.dispatchEvent(new CustomEvent("themechange", { detail: { theme: next } }));
}

/* Action Queue: populate side detail panel on row click */
function selectQueueRow(rowEl, isUserClick = true) {
  document.querySelectorAll("tr.clickable").forEach(r => r.classList.remove("selected"));
  rowEl.classList.add("selected");

  const d = JSON.parse(rowEl.dataset.action);
  const panel = document.getElementById("detail-content");
  if (!panel) return;

  const reasonsHtml = d.reasons.length
    ? d.reasons.map(([text, pts]) => `<li><span>${text}</span><strong>+${pts}</strong></li>`).join("")
    : `<li><span>No urgency factors active</span><strong>+0</strong></li>`;

  const stages = ["Applied", "Shortlisted", "Interview", "Offer", "Hired", "Rejected"];
  const stageOptions = stages
    .map(s => `<option value="${s}" ${s === d.stage ? "selected" : ""}>${s}</option>`)
    .join("");

  const actionBtns = d.status === "Pending"
    ? `<div class="btn-row">
         <button class="success" onclick="completeAction(${d.action_id})">Mark Complete</button>
         <button onclick="snoozeAction(${d.action_id}, 1)">Snooze +1d</button>
         <button onclick="snoozeAction(${d.action_id}, 3)">Snooze +3d</button>
       </div>`
    : `<p class="muted">Completed on ${d.completed_at || "—"}</p>`;

  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
      <span class="badge badge-${d.priority}">${d.priority} (${d.score}/45)</span>
      <a href="/candidates/${d.candidate_id}" class="muted">Open Candidate →</a>
    </div>
    <h2 style="margin-top:10px;">${d.action_type}</h2>
    <p class="muted" style="margin:0 0 10px;">${d.description || "No additional notes."}</p>
    <p style="font-size:0.88rem;margin:4px 0;"><strong>Candidate:</strong> ${d.candidate}</p>
    <p style="font-size:0.88rem;margin:4px 0;"><strong>Job:</strong> ${d.job_title} (${d.job_priority})</p>
    <p style="font-size:0.88rem;margin:4px 0;"><strong>Recruiter:</strong> ${d.recruiter}</p>
    <p style="font-size:0.88rem;margin:4px 0;"><strong>Due:</strong> ${d.due_at} · <strong>Waiting:</strong> ${d.waiting_days}d</p>

    <h3 style="font-size:0.85rem;margin:14px 0 4px;">Why this priority</h3>
    <ul class="reason-list">${reasonsHtml}</ul>

    ${actionBtns}

    <label style="display:block;font-size:0.8rem;color:var(--muted);margin-top:10px;">
      Move Pipeline Stage
      <select style="width:100%;margin-top:4px;" onchange="updateStage(${d.application_id}, this.value)">
        ${stageOptions}
      </select>
    </label>
  `;

  /* On mobile/tablet, smoothly scroll down to the stacked detail panel when tapped */
  if (isUserClick && window.innerWidth <= 1024) {
    const detailAside = panel.closest(".detail-panel");
    if (detailAside) {
      detailAside.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  syncThemeButton();
  const firstRow = document.querySelector("tr.clickable");
  if (firstRow) selectQueueRow(firstRow, false);
});
