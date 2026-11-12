const controls = [...document.querySelectorAll("[data-filter]")];
const messages = [...document.querySelectorAll("#sample-inbox [data-kind]")];
const status = document.querySelector("#demo-status");
const count = document.querySelector("#result-count");
const sampleRowsToggle = document.querySelector("#sample-rows-toggle");
const sampleRows = document.querySelector("#sample-rows");

for (const control of controls) {
  control.addEventListener("click", () => {
    const filter = control.dataset.filter;
    let visible = 0;
    for (const message of messages) {
      const show = filter === "all" || message.dataset.kind === filter;
      message.hidden = !show;
      visible += Number(show);
    }
    for (const button of controls) button.setAttribute("aria-pressed", String(button === control));
    const label = filter === "match" ? "job signal" : filter === "noise" ? "filtered message" : "synthetic message";
    status.textContent = `Showing ${filter === "all" ? "all " : ""}${visible} ${label}${visible === 1 ? "" : "s"}.`;
    count.textContent = String(visible).padStart(2, "0");
  });
}

sampleRowsToggle.addEventListener("click", () => {
  const open = sampleRowsToggle.getAttribute("aria-expanded") === "true";
  sampleRowsToggle.setAttribute("aria-expanded", String(!open));
  sampleRows.hidden = open;
  sampleRowsToggle.innerHTML = open
    ? 'Preview 2 sample sheet rows <span aria-hidden="true">↓</span>'
    : 'Hide sample sheet rows <span aria-hidden="true">↑</span>';
  status.textContent = open
    ? "Sample sheet preview hidden."
    : "Showing two fictional job rows; message bodies are not stored by default.";
});
