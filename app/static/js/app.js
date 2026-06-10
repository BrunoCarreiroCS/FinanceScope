// FinanceScope - interacoes de interface.

document.addEventListener("DOMContentLoaded", () => {
  console.debug("FinanceScope UI pronta");
  initHourlyPreview();
  initDashboardCharts();
  initUserMenu();
  initMobileSidebar();
});

// Sidebar off-canvas no mobile: abre/fecha via hamburguer + overlay.
function initMobileSidebar() {
  const btn = document.getElementById("hamburgerBtn");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");
  if (!btn || !sidebar || !overlay) return;

  const open = () => {
    sidebar.classList.add("is-open");
    overlay.classList.add("is-open");
    btn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden"; // trava scroll de fundo
  };
  const close = () => {
    sidebar.classList.remove("is-open");
    overlay.classList.remove("is-open");
    btn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  };

  btn.addEventListener("click", () => {
    sidebar.classList.contains("is-open") ? close() : open();
  });
  overlay.addEventListener("click", close);
  // Fecha ao clicar em qualquer link do menu (UX no mobile).
  sidebar.querySelectorAll(".nav-item").forEach((a) => a.addEventListener("click", close));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar.classList.contains("is-open")) close();
  });
  // Girar o celular pra paisagem (ou redimensionar pra desktop) com o menu
  // aberto deixaria sidebar + overlay travados sobre o layout — fecha.
  window.addEventListener("resize", () => {
    if (window.innerWidth > 880 && sidebar.classList.contains("is-open")) close();
  });
}

// Menu do avatar (canto superior direito): abre/fecha no clique,
// fecha ao clicar fora ou apertar Esc.
function initUserMenu() {
  const btn = document.getElementById("avatarBtn");
  const menu = document.getElementById("userDropdown");
  if (!btn || !menu) return;

  const close = () => {
    menu.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  };
  const toggle = () => {
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  };

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggle();
  });
  document.addEventListener("click", (e) => {
    if (!menu.hidden && !menu.contains(e.target)) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

// Paleta e helpers compartilhados com o CSS (mantidos em sincronia na mao).
const CORES = {
  texto: "#7e8a99",
  grade: "rgba(255,255,255,0.06)",
  alta: "#16c784",
  baixa: "#f6465d",
};

function moeda(v) {
  return "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2 });
}

// Dashboard: renderiza o donut de categorias e a linha de evolucao mensal.
function initDashboardCharts() {
  const raw = document.getElementById("dash-data");
  if (!raw || typeof Chart === "undefined") return;

  let data;
  try {
    data = JSON.parse(raw.textContent);
  } catch (e) {
    console.warn("Falha ao ler dados do dashboard", e);
    return;
  }

  Chart.defaults.color = CORES.texto;
  Chart.defaults.font.family = "Geist, Inter, system-ui, sans-serif";

  // Donut: gastos por categoria.
  const catEl = document.getElementById("catChart");
  if (catEl && data.categories.values.length) {
    new Chart(catEl, {
      type: "doughnut",
      data: {
        labels: data.categories.labels,
        datasets: [{
          data: data.categories.values,
          backgroundColor: data.categories.colors,
          borderColor: "#151b24",
          borderWidth: 3,
        }],
      },
      options: {
        cutout: "64%",
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => " " + c.label + ": " + moeda(c.parsed) } },
        },
      },
    });
  }

  // Linha: receitas x despesas nos ultimos meses.
  const evoEl = document.getElementById("evoChart");
  if (evoEl) {
    new Chart(evoEl, {
      type: "line",
      data: {
        labels: data.evolution.labels,
        datasets: [
          {
            label: "Receitas", data: data.evolution.income,
            borderColor: CORES.alta, backgroundColor: "rgba(22,199,132,0.12)",
            fill: true, tension: 0.35, pointRadius: 3,
          },
          {
            label: "Despesas", data: data.evolution.expense,
            borderColor: CORES.baixa, backgroundColor: "rgba(246,70,93,0.10)",
            fill: true, tension: 0.35, pointRadius: 3,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: { callbacks: { label: (c) => c.dataset.label + ": " + moeda(c.parsed.y) } },
        },
        scales: {
          x: { grid: { color: CORES.grade } },
          y: {
            grid: { color: CORES.grade },
            ticks: { callback: (v) => "R$ " + v.toLocaleString("pt-BR") },
          },
        },
      },
    });
  }
}

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
