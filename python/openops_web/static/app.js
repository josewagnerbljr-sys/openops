// AI assistance (CS50 final-project policy): written with Claude (Anthropic). See README.md, section 6.
/*
 * OpenOps — micro-site (JavaScript puro, sem bibliotecas, sem CDN).
 *
 * Regra de ouro de segurança: todo texto vindo do servidor entra na tela
 * por `textContent` (via o helper `h`), nunca por `innerHTML`. Assim, um
 * nome de produto como "<img onerror=...>" aparece como texto inofensivo.
 *
 * Uso de IA (política do CS50 para o projeto final): escrito com a assistência da IA
 * Claude (Anthropic). O problema e os requisitos são do autor; a implementação foi
 * escrita com a IA. Veja README.md, seção 6.
 */
"use strict";

/* ------------------------------------------------------------------ i18n */
const I18N = {
  pt: {
    appName: "OpenOps", dashboard: "Painel", products: "Produtos", movements: "Movimentações",
    customers: "Clientes", users: "Usuários", logout: "Sair", password: "Senha", language: "English",
    signIn: "Entrar", username: "Usuário", pass: "Senha", passConfirm: "Repita a senha",
    setupTitle: "Crie o primeiro acesso", setupLead: "Este usuário será o administrador do sistema.",
    setupBtn: "Criar administrador e entrar", loginTitle: "Entrar no OpenOps",
    passMismatch: "As senhas não são iguais.",
    hello: "Olá", role_viewer: "Consulta", role_operator: "Operador", role_admin: "Administrador",
    dashLead: "Situação do estoque agora.", totProducts: "Produtos", totUnits: "Unidades em estoque",
    totValue: "Valor em estoque", totAlerts: "Precisam de atenção",
    lowStock: "Estoque baixo", lowStockNone: "Nenhum produto com estoque baixo.",
    expiring: "Lotes perto do vencimento (30 dias)", expiringNone: "Nenhum lote vencendo nos próximos 30 dias.",
    expiringNote: "Lotes recebidos com validade próxima; confira a prateleira.",
    recent: "Últimas movimentações", recentNone: "Ainda não há movimentações.",
    restock: "Repor", units: "un.", daysLeft: "dias", expired: "vencido",
    productsLead: "Cadastre produtos e registre entradas e saídas direto na linha.",
    search: "Buscar produto ou categoria", allCategories: "Todas as categorias",
    newProduct: "Novo produto", exportCsv: "Baixar planilha (CSV)",
    colProduct: "Produto", colCategory: "Categoria", colPrice: "Preço", colStock: "Estoque", colQuick: "Entrada / saída", colMore: "",
    entry: "Entrada", exit: "Saída", more: "Mais", noProducts: "Nenhum produto ainda. Use “Novo produto” para começar.",
    noMatch: "Nenhum produto encontrado para essa busca.",
    fName: "Nome do produto", fPrice: "Preço (R$)", fCategory: "Categoria", fInitial: "Estoque inicial",
    fInitialHint: "Opcional. Entra no histórico como “Estoque inicial”.", fQty: "Quantidade",
    fReason: "Motivo (opcional)", fBatch: "Lote (opcional)", fExpiry: "Validade (opcional)",
    save: "Salvar", cancel: "Cancelar", close: "Fechar", create: "Criar", remove: "Remover", edit: "Editar",
    entryWithBatch: "Entrada com lote e validade", adjust: "Corrigir contagem (inventário)",
    adjustHint: "Informe a quantidade real contada. O estoque passa a ser exatamente esse número.",
    adjustQty: "Quantidade contada", editProduct: "Editar produto",
    removeTitle: "Remover produto", removeAsk: "Remover “{n}” do catálogo?",
    removeNote: "Se o produto já tem histórico, ele será arquivado: some da lista, mas as movimentações antigas são mantidas.",
    removedDeleted: "Produto “{n}” apagado.", removedArchived: "Produto “{n}” arquivado (o histórico foi mantido).",
    moved_in: "Entrada de {q} em {n}. Estoque: {s}.", moved_out: "Saída de {q} em {n}. Estoque: {s}.",
    moved_adjustment: "Contagem de {n} corrigida. Estoque: {s}.", created: "Salvo.", qtyInvalid: "Informe uma quantidade inteira maior que zero.",
    movLead: "Histórico completo de entradas, saídas e correções.", allProducts: "Todos os produtos",
    colDate: "Data", colType: "Tipo", colQtyShort: "Qtd.", colReason: "Motivo", colBatch: "Lote", colExpiry: "Validade",
    type_in: "Entrada", type_out: "Saída", type_adjustment: "Correção",
    custLead: "Quem compra de você.", newCustomer: "Novo cliente", colName: "Nome", colEmail: "E-mail", colPhone: "Telefone", colDoc: "Documento",
    fEmail: "E-mail", fPhone: "Telefone", fDoc: "CPF/CNPJ", noCustomers: "Nenhum cliente cadastrado.", editCustomer: "Editar cliente",
    removeCustomerAsk: "Remover o cliente “{n}”?",
    usersLead: "Quem pode entrar e o que cada pessoa pode fazer.", newUser: "Novo usuário", colUser: "Usuário", colRole: "Papel", colLast: "Último acesso",
    never: "nunca", roleHelp: "Consulta só vê. Operador também cadastra e movimenta. Administrador também gerencia usuários.",
    removeUserAsk: "Apagar o usuário “{n}”?", changePassword: "Trocar senha", curPass: "Senha atual", newPass: "Nova senha",
    passChanged: "Senha alterada.", loading: "Carregando…", sessionEnded: "Sua sessão terminou. Entre novamente.",
    netError: "Não foi possível falar com o servidor. Confira se o OpenOps ainda está rodando.",
    lowTag: "baixo", outTag: "zerado", updated: "Atualizado.",
  },
  en: {
    appName: "OpenOps", dashboard: "Dashboard", products: "Products", movements: "Movements",
    customers: "Customers", users: "Users", logout: "Sign out", password: "Password", language: "Português",
    signIn: "Sign in", username: "Username", pass: "Password", passConfirm: "Repeat password",
    setupTitle: "Create the first account", setupLead: "This user will be the system administrator.",
    setupBtn: "Create administrator and sign in", loginTitle: "Sign in to OpenOps",
    passMismatch: "The passwords do not match.",
    hello: "Hi", role_viewer: "View only", role_operator: "Operator", role_admin: "Administrator",
    dashLead: "Stock situation right now.", totProducts: "Products", totUnits: "Units in stock",
    totValue: "Stock value", totAlerts: "Need attention",
    lowStock: "Low stock", lowStockNone: "No product is running low.",
    expiring: "Batches close to expiry (30 days)", expiringNone: "No batch expires in the next 30 days.",
    expiringNote: "Received batches with a near expiry date; check the shelf.",
    recent: "Latest movements", recentNone: "No movements yet.",
    restock: "Restock", units: "pcs", daysLeft: "days", expired: "expired",
    productsLead: "Add products and record stock in and out right on the row.",
    search: "Search product or category", allCategories: "All categories",
    newProduct: "New product", exportCsv: "Download spreadsheet (CSV)",
    colProduct: "Product", colCategory: "Category", colPrice: "Price", colStock: "Stock", colQuick: "Stock in / out", colMore: "",
    entry: "Add", exit: "Remove", more: "More", noProducts: "No products yet. Use “New product” to start.",
    noMatch: "No product matches this search.",
    fName: "Product name", fPrice: "Price (R$)", fCategory: "Category", fInitial: "Initial stock",
    fInitialHint: "Optional. Logged in the history as “Initial stock”.", fQty: "Quantity",
    fReason: "Reason (optional)", fBatch: "Batch (optional)", fExpiry: "Expiry date (optional)",
    save: "Save", cancel: "Cancel", close: "Close", create: "Create", remove: "Remove", edit: "Edit",
    entryWithBatch: "Stock in with batch and expiry", adjust: "Correct count (inventory)",
    adjustHint: "Enter the real counted quantity. Stock becomes exactly that number.",
    adjustQty: "Counted quantity", editProduct: "Edit product",
    removeTitle: "Remove product", removeAsk: "Remove “{n}” from the catalog?",
    removeNote: "If the product already has history it is archived: it leaves the list but past movements are kept.",
    removedDeleted: "Product “{n}” deleted.", removedArchived: "Product “{n}” archived (history kept).",
    moved_in: "Added {q} to {n}. Stock: {s}.", moved_out: "Removed {q} from {n}. Stock: {s}.",
    moved_adjustment: "Count of {n} corrected. Stock: {s}.", created: "Saved.", qtyInvalid: "Enter a whole number greater than zero.",
    movLead: "Full history of stock in, out and corrections.", allProducts: "All products",
    colDate: "Date", colType: "Type", colQtyShort: "Qty", colReason: "Reason", colBatch: "Batch", colExpiry: "Expiry",
    type_in: "In", type_out: "Out", type_adjustment: "Correction",
    custLead: "People who buy from you.", newCustomer: "New customer", colName: "Name", colEmail: "Email", colPhone: "Phone", colDoc: "Document",
    fEmail: "Email", fPhone: "Phone", fDoc: "Tax ID", noCustomers: "No customers yet.", editCustomer: "Edit customer",
    removeCustomerAsk: "Remove customer “{n}”?",
    usersLead: "Who can sign in and what each person can do.", newUser: "New user", colUser: "User", colRole: "Role", colLast: "Last sign-in",
    never: "never", roleHelp: "View only can look. Operator can also add and move stock. Administrator also manages users.",
    removeUserAsk: "Delete user “{n}”?", changePassword: "Change password", curPass: "Current password", newPass: "New password",
    passChanged: "Password changed.", loading: "Loading…", sessionEnded: "Your session ended. Please sign in again.",
    netError: "Could not reach the server. Check that OpenOps is still running.",
    lowTag: "low", outTag: "empty", updated: "Updated.",
  },
};

/* ------------------------------------------------------------------ estado */
const state = { token: null, user: null, lang: "pt", status: null, view: "dashboard", threshold: 5 };

function safeStorage(kind) {
  try { return window[kind]; } catch (_) { return null; }
}
function load(kind, key) { try { return safeStorage(kind)?.getItem(key) ?? null; } catch (_) { return null; } }
function save(kind, key, value) {
  try {
    const store = safeStorage(kind);
    if (!store) return;
    if (value === null) store.removeItem(key); else store.setItem(key, value);
  } catch (_) { /* armazenamento indisponível: tudo continua funcionando sem ele */ }
}

state.lang = load("localStorage", "openops.lang") || ((navigator.language || "pt").startsWith("en") ? "en" : "pt");
state.token = load("sessionStorage", "openops.token");

const t = (key, vars = {}) =>
  (I18N[state.lang][key] ?? I18N.pt[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ""));

const money = (v) => new Intl.NumberFormat(state.lang === "pt" ? "pt-BR" : "en-US", { style: "currency", currency: "BRL" }).format(v);
const intFmt = (v) => new Intl.NumberFormat(state.lang === "pt" ? "pt-BR" : "en-US").format(v);
const dateFmt = (iso) => (iso ? new Date(iso.length === 10 ? iso + "T12:00:00" : iso).toLocaleDateString(state.lang === "pt" ? "pt-BR" : "en-US") : "");
const dateTimeFmt = (iso) => (iso ? new Date(iso).toLocaleString(state.lang === "pt" ? "pt-BR" : "en-US", { dateStyle: "short", timeStyle: "short" }) : "");

/* ------------------------------------------------------------------ DOM */
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k in el && k !== "list") el[k] = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const $app = () => document.getElementById("app");

function toast(message, kind = "ok") {
  const box = h("div", { class: "toast" + (kind === "error" ? " error" : "") }, message);
  document.getElementById("toasts").append(box);
  setTimeout(() => box.remove(), kind === "error" ? 7000 : 3500);
}

/* ------------------------------------------------------------------ API */
class ApiError extends Error {
  constructor(status, body) {
    super(body?.message || "Erro");
    this.status = status;
    this.code = body?.error;
    this.details = body?.details || {};
  }
}

async function api(path, { method = "GET", body, raw = false } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (state.token) headers["Authorization"] = "Bearer " + state.token;
  let response;
  try {
    response = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch (_) {
    throw new ApiError(0, { message: t("netError") });
  }
  if (raw && response.ok) return response;
  let data = null;
  try { data = await response.json(); } catch (_) { /* resposta sem corpo */ }
  if (!response.ok) {
    if (response.status === 401 && state.token) {
      logout(true);
    }
    throw new ApiError(response.status, data);
  }
  return data;
}

const can = (role) => ({ viewer: 1, operator: 2, admin: 3 }[state.user?.role] || 0) >= { viewer: 1, operator: 2, admin: 3 }[role];

/* ------------------------------------------------------------------ diálogos */
function fieldRow(f) {
  const id = "f-" + f.name;
  let control;
  if (f.type === "select") {
    control = h("select", { id, name: f.name }, f.options.map((o) => h("option", { value: o.value, selected: o.value === f.value }, o.label)));
  } else {
    control = h("input", {
      id, name: f.name, type: f.type || "text", value: f.value ?? "", required: !!f.required,
      min: f.min, step: f.step, maxLength: f.maxLength, autocomplete: f.autocomplete || "off", inputMode: f.inputMode,
    });
  }
  return h("div", { class: "field" }, h("label", { for: id }, f.label), control,
    f.hint ? h("span", { class: "hint" }, f.hint) : null,
    h("span", { class: "err", id: id + "-err", hidden: true }));
}

function openDialog({ title, fields = [], intro, submitLabel, danger = false, onSubmit, extra }) {
  return new Promise((resolve) => {
    const errBox = h("div", { class: "form-error", hidden: true, role: "alert" });
    const submit = h("button", { class: "btn " + (danger ? "danger" : "primary"), type: "submit" }, submitLabel || t("save"));
    const form = h("form", { method: "dialog", novalidate: true },
      h("h2", {}, title), intro ? h("p", { class: "muted" }, intro) : null, errBox, fields.map(fieldRow), extra || null,
      h("div", { class: "dlg-actions" },
        h("button", { class: "btn", type: "button", onclick: () => dlg.close() }, t("cancel")), submit));
    const dlg = h("dialog", { "aria-label": title }, form);
    dlg.addEventListener("close", () => { dlg.remove(); resolve(); });
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      errBox.hidden = true;
      form.querySelectorAll(".err").forEach((e) => { e.hidden = true; });
      form.querySelectorAll("[aria-invalid]").forEach((e) => e.removeAttribute("aria-invalid"));
      const values = Object.fromEntries(new FormData(form).entries());
      submit.disabled = true;
      try {
        await onSubmit(values);
        dlg.close();
      } catch (err) {
        showFormError(err, form, errBox);
        submit.disabled = false;
      }
    });
    document.body.append(dlg);
    dlg.showModal();
    form.querySelector("input, select")?.focus();
  });
}

function showFormError(err, form, errBox) {
  const details = err instanceof ApiError ? err.details : {};
  let shown = false;
  for (const [field, msg] of Object.entries(details)) {
    const slot = form.querySelector("#f-" + field + "-err");
    if (slot && typeof msg === "string") {
      slot.textContent = msg; slot.hidden = false; shown = true;
      form.querySelector("#f-" + field)?.setAttribute("aria-invalid", "true");
    }
  }
  if (!shown || !(err instanceof ApiError) || err.status !== 422) {
    errBox.textContent = err.message; errBox.hidden = false;
  }
}

function confirmDialog({ title, message, note, confirmLabel, onConfirm }) {
  return openDialog({
    title, intro: message, submitLabel: confirmLabel, danger: true, onSubmit: onConfirm,
    extra: note ? h("p", { class: "muted" }, note) : null,
  });
}

/* ------------------------------------------------------------------ sessão */
function logout(expired = false) {
  state.token = null; state.user = null;
  save("sessionStorage", "openops.token", null);
  boot().then(() => { if (expired) toast(t("sessionEnded"), "error"); });
}

function setSession(data) {
  state.token = data.token; state.user = data.user;
  save("sessionStorage", "openops.token", data.token);
}

function renderAuth(setup) {
  const err = h("div", { class: "form-error", hidden: true, role: "alert" });
  const form = h("form", { novalidate: true },
    h("div", { class: "field" }, h("label", { for: "u" }, t("username")),
      h("input", { id: "u", name: "username", autocomplete: "username", required: true, autofocus: true })),
    h("div", { class: "field" }, h("label", { for: "p" }, t("pass")),
      h("input", { id: "p", name: "password", type: "password", autocomplete: setup ? "new-password" : "current-password", required: true })),
    setup ? h("div", { class: "field" }, h("label", { for: "p2" }, t("passConfirm")),
      h("input", { id: "p2", name: "password2", type: "password", autocomplete: "new-password", required: true })) : null,
    err,
    h("button", { class: "btn primary", type: "submit" }, setup ? t("setupBtn") : t("signIn")));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.hidden = true;
    const v = Object.fromEntries(new FormData(form).entries());
    if (setup && v.password !== v.password2) { err.textContent = t("passMismatch"); err.hidden = false; return; }
    try {
      const data = await api(setup ? "/api/setup" : "/api/login", { method: "POST", body: { username: v.username, password: v.password } });
      setSession(data);
      await boot();
    } catch (e) { err.textContent = e.message; err.hidden = false; }
  });
  $app().replaceChildren(h("div", { class: "auth" }, h("div", { class: "auth-box" },
    h("div", { class: "brand" }, h("img", { src: "/static/favicon.svg", alt: "" }), t("appName")),
    h("h1", {}, setup ? t("setupTitle") : t("loginTitle")),
    setup ? h("p", { class: "lead" }, t("setupLead")) : null, form,
    h("p", {}, h("button", { class: "btn link", type: "button", onclick: toggleLang }, t("language"))))));
}

function toggleLang() {
  state.lang = state.lang === "pt" ? "en" : "pt";
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  save("localStorage", "openops.lang", state.lang);
  boot();
}

/* ------------------------------------------------------------------ estrutura */
const VIEWS = {
  dashboard: () => viewDashboard(),
  products: () => viewProducts(),
  movements: () => viewMovements(),
  customers: () => viewCustomers(),
  users: () => viewUsers(),
};

function renderShell() {
  const names = ["dashboard", "products", "movements", "customers"].concat(can("admin") ? ["users"] : []);
  const nav = h("nav", { class: "nav", "aria-label": "Principal" }, names.map((n) =>
    h("button", { type: "button", "aria-current": state.view === n ? "page" : null, onclick: () => go(n) }, t(n))));
  const header = h("header", { class: "top" }, h("div", { class: "top-inner" },
    h("div", { class: "brand" }, h("img", { src: "/static/favicon.svg", alt: "" }), t("appName")), nav,
    h("div", { class: "who" },
      h("span", {}, t("hello") + ", ", h("strong", {}, state.user.username), " (" + t("role_" + state.user.role) + ")"),
      h("button", { class: "btn link", type: "button", onclick: changePasswordDialog }, t("password")),
      h("button", { class: "btn link", type: "button", onclick: toggleLang }, t("language")),
      h("button", { class: "btn link", type: "button", onclick: () => logout() }, t("logout")))));
  $app().replaceChildren(header, h("main", { id: "main", tabIndex: -1 }, h("p", { class: "muted" }, t("loading"))));
}

async function go(view) {
  state.view = view;
  renderShell();
  await renderView();
}

async function renderView() {
  const main = document.getElementById("main");
  try {
    const node = await VIEWS[state.view]();
    main.replaceChildren(...[].concat(node));
  } catch (e) {
    if (e.status !== 401) main.replaceChildren(h("div", { class: "form-error" }, e.message));
  }
}

/* ------------------------------------------------------------------ painel */
async function viewDashboard() {
  const d = await api("/api/dashboard");
  state.threshold = d.low_stock_threshold;
  const alerts = d.totals.low_stock + d.totals.expiring_soon;
  const fig = (n, label, warn) => h("div", { class: warn ? "warn" : "" }, h("span", { class: "n" }, n), h("span", { class: "l" }, label));
  const lowList = d.low_stock.length
    ? h("ul", { class: "plain-list" }, d.low_stock.map((p) => h("li", {},
        h("span", {}, h("strong", {}, p.name), h("br"), h("span", { class: "sub" }, `${intFmt(p.stock)} ${t("units")}` + (p.category ? ` · ${p.category}` : ""))),
        can("operator") ? h("button", { class: "btn small", type: "button", onclick: () => stockDialog(p, "in", renderView) }, t("restock")) : null)))
    : h("p", { class: "empty" }, t("lowStockNone"));
  const expList = d.expiring.length
    ? h("ul", { class: "plain-list" }, d.expiring.map((b) => h("li", {},
        h("span", {}, h("strong", {}, b.product_name), h("br"),
          h("span", { class: "sub" }, (b.batch_number ? `${b.batch_number} · ` : "") + dateFmt(b.expiry_date))),
        h("span", { class: "tag " + (b.days_remaining < 0 ? "out" : "low") }, b.days_remaining < 0 ? t("expired") : `${b.days_remaining} ${t("daysLeft")}`))))
    : h("p", { class: "empty" }, t("expiringNone"));
  const recent = d.recent_movements.length
    ? h("ul", { class: "plain-list" }, d.recent_movements.map((m) => h("li", {},
        h("span", {}, h("strong", {}, m.product_name), h("br"), h("span", { class: "sub" }, dateTimeFmt(m.created_at) + (m.reason ? ` · ${m.reason}` : ""))),
        h("span", { class: "tag " + (m.type === "out" ? "low" : "") }, `${t("type_" + m.type)} ${intFmt(m.quantity)}`))))
    : h("p", { class: "empty" }, t("recentNone"));
  return [
    h("h1", {}, t("dashboard")), h("p", { class: "lead" }, t("dashLead")),
    h("div", { class: "ledger" },
      fig(intFmt(d.totals.products), t("totProducts")), fig(intFmt(d.totals.units), t("totUnits")),
      fig(money(d.totals.stock_value), t("totValue")), fig(intFmt(alerts), t("totAlerts"), alerts > 0)),
    h("div", { class: "cols" },
      h("section", {}, h("h2", {}, t("lowStock")), lowList),
      h("section", {}, h("h2", {}, t("expiring")), h("p", { class: "muted" }, t("expiringNote")), expList)),
    h("section", {}, h("h2", {}, t("recent")), recent),
  ];
}

/* ------------------------------------------------------------------ produtos */
let productFilter = { q: "", category: "" };

async function viewProducts() {
  const data = await api("/api/products");
  state.threshold = data.low_stock_threshold;
  const search = h("input", { type: "search", class: "grow", placeholder: t("search"), "aria-label": t("search"), value: productFilter.q });
  const cat = h("select", { "aria-label": t("allCategories") },
    h("option", { value: "" }, t("allCategories")),
    data.categories.map((c) => h("option", { value: c, selected: c === productFilter.category }, c)));
  const body = h("div", {});
  const redraw = () => {
    productFilter = { q: search.value, category: cat.value };
    const q = search.value.trim().toLowerCase();
    const rows = data.products.filter((p) => (!cat.value || p.category === cat.value) && (!q || p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q)));
    body.replaceChildren(productTable(rows, data.products.length === 0));
  };
  search.addEventListener("input", redraw);
  cat.addEventListener("change", redraw);
  redraw();
  const exportBtn = h("button", { class: "btn", type: "button", onclick: () => downloadCsv("/api/export/products.csv", "produtos.csv") }, t("exportCsv"));
  return [
    h("h1", {}, t("products")), h("p", { class: "lead" }, t("productsLead")),
    h("div", { class: "toolbar" }, h("div", { class: "grow" }, search), cat, exportBtn,
      can("operator") ? h("button", { class: "btn primary", type: "button", onclick: () => newProductDialog() }, t("newProduct")) : null),
    body,
  ];
}

function productTable(rows, none) {
  if (!rows.length) return h("p", { class: "empty" }, none ? t("noProducts") : t("noMatch"));
  const maxStock = Math.max(state.threshold * 3, ...rows.map((p) => p.stock));
  const tbody = h("tbody", {}, rows.map((p) => productRow(p, maxStock)));
  return h("div", { class: "table-wrap stack" }, h("table", {},
    h("thead", {}, h("tr", {}, h("th", {}, t("colProduct")), h("th", {}, t("colCategory")), h("th", { class: "num" }, t("colPrice")),
      h("th", {}, t("colStock")), can("operator") ? h("th", {}, t("colQuick")) : null, can("operator") ? h("th", {}, "") : null)), tbody));
}

function productRow(p, maxStock) {
  const status = p.stock === 0 ? "out" : p.low_stock ? "low" : "";
  const gauge = h("span", { class: "gauge " + status }, h("span", {}));
  gauge.firstChild.style.setProperty("--w", Math.max(p.stock > 0 ? 4 : 0, Math.min(100, (p.stock / maxStock) * 100)) + "%");
  const qty = h("input", { type: "number", min: "1", step: "1", value: "1", inputMode: "numeric", "aria-label": t("fQty") + " — " + p.name });
  const quick = (type, label, cls) => h("button", {
    class: "btn small " + cls, type: "button",
    onclick: async (ev) => {
      const button = ev.currentTarget; // guardar já: depois de um `await` o navegador zera currentTarget
      const n = Number(qty.value);
      if (!Number.isInteger(n) || n < 1) { toast(t("qtyInvalid"), "error"); qty.focus(); return; }
      button.disabled = true;
      try { await quickMove(p, type, n); } catch (e) { toast(e.message, "error"); button.disabled = false; }
    },
  }, label);
  return h("tr", {},
    h("td", { class: "c-name" }, h("strong", {}, p.name)), h("td", { class: "c-cat muted" }, p.category || "—"), h("td", { class: "c-price num" }, money(p.price)),
    h("td", { class: "c-level" }, h("div", { class: "level" }, gauge, h("b", {}, intFmt(p.stock)),
      status ? h("span", { class: "tag " + status }, status === "out" ? t("outTag") : t("lowTag")) : null)),
    can("operator") ? h("td", { class: "c-quick" }, h("div", { class: "quick" }, qty, quick("in", "+ " + t("entry"), "in"), quick("out", "− " + t("exit"), "out"))) : null,
    can("operator") ? h("td", { class: "c-more" }, h("button", { class: "btn small", type: "button", onclick: () => moreDialog(p) }, t("more"))) : null);
}

async function quickMove(p, type, quantity) {
  const r = await api("/api/stock", { method: "POST", body: { product_id: p.id, type, quantity } });
  toast(t("moved_" + type, { q: intFmt(quantity), n: p.name, s: intFmt(r.product.stock) }));
  await renderView();
}

function newProductDialog() {
  return openDialog({
    title: t("newProduct"), submitLabel: t("create"),
    fields: [
      { name: "name", label: t("fName"), required: true, maxLength: 120 },
      { name: "price", label: t("fPrice"), type: "number", min: "0.01", step: "0.01", required: true, inputMode: "decimal" },
      { name: "category", label: t("fCategory"), maxLength: 60 },
      { name: "stock", label: t("fInitial"), type: "number", min: "0", step: "1", value: "0", hint: t("fInitialHint") },
    ],
    onSubmit: async (v) => {
      await api("/api/products", { method: "POST", body: { name: v.name, price: Number(v.price), category: v.category, stock: Number(v.stock || 0) } });
      toast(t("created")); await renderView();
    },
  });
}

function stockDialog(p, type, after) {
  const withBatch = type === "in";
  const fields = [{ name: "quantity", label: type === "adjustment" ? t("adjustQty") : t("fQty"), type: "number", min: type === "adjustment" ? "0" : "1", step: "1", required: true, value: type === "adjustment" ? String(p.stock) : "", hint: type === "adjustment" ? t("adjustHint") : null }];
  fields.push({ name: "reason", label: t("fReason"), maxLength: 200 });
  if (withBatch) fields.push({ name: "batch_number", label: t("fBatch"), maxLength: 60 }, { name: "expiry_date", label: t("fExpiry"), type: "date" });
  return openDialog({
    title: (type === "in" ? t("entry") : type === "out" ? t("exit") : t("adjust")) + " — " + p.name, fields,
    onSubmit: async (v) => {
      const q = Number(v.quantity);
      if (!Number.isInteger(q)) throw new ApiError(422, { message: t("qtyInvalid"), error: "validation_error", details: { quantity: t("qtyInvalid") } });
      const body = { product_id: p.id, type, quantity: q, reason: v.reason || "" };
      if (withBatch) { body.batch_number = v.batch_number || ""; body.expiry_date = v.expiry_date || ""; }
      const r = await api("/api/stock", { method: "POST", body });
      toast(t("moved_" + type, { q: intFmt(q), n: p.name, s: intFmt(r.product.stock) }));
      await after();
    },
  });
}

function editProductDialog(p) {
  return openDialog({
    title: t("editProduct"),
    fields: [
      { name: "name", label: t("fName"), required: true, value: p.name, maxLength: 120 },
      { name: "price", label: t("fPrice"), type: "number", min: "0.01", step: "0.01", required: true, value: String(p.price), inputMode: "decimal" },
      { name: "category", label: t("fCategory"), value: p.category, maxLength: 60 },
    ],
    onSubmit: async (v) => {
      await api("/api/products/" + p.id, { method: "PUT", body: { name: v.name, price: Number(v.price), category: v.category } });
      toast(t("created")); await renderView();
    },
  });
}

function removeProductDialog(p) {
  return confirmDialog({
    title: t("removeTitle"), message: t("removeAsk", { n: p.name }), note: t("removeNote"), confirmLabel: t("remove"),
    onConfirm: async () => {
      const r = await api("/api/products/" + p.id, { method: "DELETE" });
      toast(t(r.result === "archived" ? "removedArchived" : "removedDeleted", { n: p.name }));
      await renderView();
    },
  });
}

function moreDialog(p) {
  const dlg = h("dialog", { "aria-label": p.name },
    h("h2", {}, p.name),
    h("div", { class: "menu-list" },
      h("button", { class: "btn", type: "button", onclick: () => { dlg.close(); stockDialog(p, "in", renderView); } }, t("entryWithBatch")),
      h("button", { class: "btn", type: "button", onclick: () => { dlg.close(); stockDialog(p, "adjustment", renderView); } }, t("adjust")),
      h("button", { class: "btn", type: "button", onclick: () => { dlg.close(); editProductDialog(p); } }, t("edit")),
      h("button", { class: "btn danger", type: "button", onclick: () => { dlg.close(); removeProductDialog(p); } }, t("remove"))),
    h("div", { class: "dlg-actions" }, h("button", { class: "btn", type: "button", onclick: () => dlg.close() }, t("close"))));
  dlg.addEventListener("close", () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
}

async function downloadCsv(path, filename) {
  try {
    const response = await api(path, { raw: true });
    const url = URL.createObjectURL(await response.blob());
    const a = h("a", { href: url, download: filename });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  } catch (e) { toast(e.message, "error"); }
}

/* ------------------------------------------------------------------ movimentações */
let movementProduct = "";

async function viewMovements() {
  const [{ products }, data] = await Promise.all([api("/api/products"), api("/api/movements" + (movementProduct ? "?product_id=" + movementProduct : ""))]);
  const sel = h("select", { "aria-label": t("allProducts") }, h("option", { value: "" }, t("allProducts")),
    products.map((p) => h("option", { value: String(p.id), selected: String(p.id) === movementProduct }, p.name)));
  sel.addEventListener("change", () => { movementProduct = sel.value; renderView(); });
  const table = data.movements.length
    ? h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, ["colDate", "colProduct", "colType", "colQtyShort", "colReason", "colBatch", "colExpiry"].map((k) => h("th", { class: k === "colQtyShort" ? "num" : "" }, t(k))))),
        h("tbody", {}, data.movements.map((m) => h("tr", {},
          h("td", { class: "muted" }, dateTimeFmt(m.created_at)), h("td", {}, h("strong", {}, m.product_name)),
          h("td", {}, h("span", { class: "tag " + (m.type === "out" ? "low" : "") }, t("type_" + m.type))),
          h("td", { class: "num" }, intFmt(m.quantity)), h("td", { class: "muted" }, m.reason || "—"),
          h("td", { class: "muted" }, m.batch_number || "—"), h("td", { class: "muted" }, m.expiry_date ? dateFmt(m.expiry_date) : "—"))))))
    : h("p", { class: "empty" }, t("recentNone"));
  return [h("h1", {}, t("movements")), h("p", { class: "lead" }, t("movLead")),
    h("div", { class: "toolbar" }, sel, h("button", { class: "btn", type: "button", onclick: () => downloadCsv("/api/export/movements.csv", "movimentacoes.csv") }, t("exportCsv"))), table];
}

/* ------------------------------------------------------------------ clientes */
async function viewCustomers() {
  const { customers } = await api("/api/customers");
  const operator = can("operator");
  const table = customers.length
    ? h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, ["colName", "colEmail", "colPhone", "colDoc"].map((k) => h("th", {}, t(k))), operator ? h("th", {}, "") : null)),
        h("tbody", {}, customers.map((c) => h("tr", {},
          h("td", {}, h("strong", {}, c.name)), h("td", { class: "muted" }, c.email || "—"), h("td", { class: "muted" }, c.phone || "—"), h("td", { class: "muted" }, c.document || "—"),
          operator ? h("td", {}, h("div", { class: "quick" },
            h("button", { class: "btn small", type: "button", onclick: () => customerDialog(c) }, t("edit")),
            h("button", { class: "btn small danger", type: "button", onclick: () => confirmDialog({ title: t("remove"), message: t("removeCustomerAsk", { n: c.name }), confirmLabel: t("remove"), onConfirm: async () => { await api("/api/customers/" + c.id, { method: "DELETE" }); toast(t("updated")); await renderView(); } }) }, t("remove")))) : null)))))
    : h("p", { class: "empty" }, t("noCustomers"));
  return [h("h1", {}, t("customers")), h("p", { class: "lead" }, t("custLead")),
    operator ? h("div", { class: "toolbar" }, h("button", { class: "btn primary", type: "button", onclick: () => customerDialog() }, t("newCustomer"))) : null, table];
}

function customerDialog(c) {
  return openDialog({
    title: c ? t("editCustomer") : t("newCustomer"), submitLabel: c ? t("save") : t("create"),
    fields: [
      { name: "name", label: t("colName"), required: true, value: c?.name, maxLength: 120 },
      { name: "email", label: t("fEmail"), type: "email", value: c?.email || "", maxLength: 120, autocomplete: "off" },
      { name: "phone", label: t("fPhone"), type: "tel", value: c?.phone || "", maxLength: 40 },
      { name: "document", label: t("fDoc"), value: c?.document || "", maxLength: 40 },
    ],
    onSubmit: async (v) => {
      await api(c ? "/api/customers/" + c.id : "/api/customers", { method: c ? "PUT" : "POST", body: v });
      toast(t("created")); await renderView();
    },
  });
}

/* ------------------------------------------------------------------ usuários */
async function viewUsers() {
  const { users } = await api("/api/users");
  const roleOptions = ["viewer", "operator", "admin"].map((r) => ({ value: r, label: t("role_" + r) }));
  const table = h("div", { class: "table-wrap" }, h("table", {},
    h("thead", {}, h("tr", {}, h("th", {}, t("colUser")), h("th", {}, t("colRole")), h("th", {}, t("colLast")), h("th", {}, ""))),
    h("tbody", {}, users.map((u) => {
      const sel = h("select", { "aria-label": t("colRole") + " — " + u.username }, roleOptions.map((o) => h("option", { value: o.value, selected: o.value === u.role }, o.label)));
      sel.addEventListener("change", async () => {
        try { await api("/api/users/" + u.id, { method: "PATCH", body: { role: sel.value } }); toast(t("updated")); await renderView(); }
        catch (e) { toast(e.message, "error"); await renderView(); }
      });
      return h("tr", {}, h("td", {}, h("strong", {}, u.username)), h("td", {}, sel),
        h("td", { class: "muted" }, u.last_login_at ? dateTimeFmt(u.last_login_at) : t("never")),
        h("td", {}, u.username.toLowerCase() === state.user.username.toLowerCase() ? null :
          h("button", { class: "btn small danger", type: "button", onclick: () => confirmDialog({ title: t("remove"), message: t("removeUserAsk", { n: u.username }), confirmLabel: t("remove"), onConfirm: async () => { await api("/api/users/" + u.id, { method: "DELETE" }); toast(t("updated")); await renderView(); } }) }, t("remove"))));
    }))));
  return [h("h1", {}, t("users")), h("p", { class: "lead" }, t("usersLead") + " " + t("roleHelp")),
    h("div", { class: "toolbar" }, h("button", { class: "btn primary", type: "button", onclick: () => newUserDialog(roleOptions) }, t("newUser"))), table];
}

function newUserDialog(roleOptions) {
  return openDialog({
    title: t("newUser"), submitLabel: t("create"),
    fields: [
      { name: "username", label: t("username"), required: true, maxLength: 32, autocomplete: "off" },
      { name: "password", label: t("pass"), type: "password", required: true, autocomplete: "new-password" },
      { name: "role", label: t("colRole"), type: "select", options: roleOptions, value: "operator" },
    ],
    onSubmit: async (v) => { await api("/api/users", { method: "POST", body: v }); toast(t("created")); await renderView(); },
  });
}

function changePasswordDialog() {
  return openDialog({
    title: t("changePassword"),
    fields: [
      { name: "current_password", label: t("curPass"), type: "password", required: true, autocomplete: "current-password" },
      { name: "new_password", label: t("newPass"), type: "password", required: true, autocomplete: "new-password" },
    ],
    onSubmit: async (v) => { await api("/api/me/password", { method: "POST", body: v }); toast(t("passChanged")); },
  });
}

/* ------------------------------------------------------------------ início */
async function boot() {
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  try {
    state.status = await api("/api/status");
    if (state.token) {
      try { state.user = (await api("/api/me")).user; } catch (_) { state.token = null; save("sessionStorage", "openops.token", null); }
    }
  } catch (e) {
    $app().replaceChildren(h("div", { class: "auth" }, h("div", { class: "auth-box" }, h("div", { class: "form-error" }, e.message))));
    return;
  }
  if (!state.user) { renderAuth(state.status.setup_required); return; }
  if (!VIEWS[state.view] || (state.view === "users" && !can("admin"))) state.view = "dashboard";
  renderShell();
  await renderView();
}

boot();
