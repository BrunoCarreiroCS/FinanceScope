// FinanceScope - interacoes de interface.

document.addEventListener("DOMContentLoaded", () => {
  console.debug("FinanceScope UI pronta");
  initHourlyPreview();
});

// Perfil: calcula "valor da hora" ao vivo (renda_mensal / horas_mensais).
function initHourlyPreview() {
  const income = document.getElementById("income");
  const hours = document.getElementById("hours");
  const out = document.getElementById("hourly-value");
  const hint = document.getElementById("hourly-hint");
  if (!income || !hours || !out) return;

  const update = () => {
    const r = parseFloat(income.value);
    const h = parseFloat(hours.value);
    if (!r || !h || h <= 0) {
      out.textContent = "—";
      if (hint) hint.textContent = "preencha renda e horas";
      return;
    }
    const value = r / h;
    out.textContent = "R$ " + value.toFixed(2).replace(".", ",");
    if (hint) hint.textContent = "por hora trabalhada/estudada";
  };

  income.addEventListener("input", update);
  hours.addEventListener("input", update);
}
