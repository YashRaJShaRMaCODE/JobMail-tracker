const controls = [...document.querySelectorAll("[data-filter]")];
const messages = [...document.querySelectorAll("#sample-inbox [data-kind]")];
const status = document.querySelector("#demo-status");
const count = document.querySelector("#result-count");

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
