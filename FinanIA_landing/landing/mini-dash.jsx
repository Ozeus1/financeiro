// Mini dashboard mock — recreates the FinanIA dashboard look from the screenshot.
// Used both in the hero (compact) and in the "Dashboard de verdade" section (with tabs).

function MdIcon({ name, className }) {
  const paths = {
    receitas: <><path d="M3 7h13l-3-3M3 7l3 3" /><rect x="9" y="11" width="12" height="9" rx="2" /><circle cx="15" cy="15.5" r="1.5" /></>,
    despesas: <><path d="M4 7l16 0" /><path d="M4 7v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" /><path d="M8 7V5a4 4 0 0 1 8 0v2" /></>,
    saldo: <><path d="M12 4c-4.4 0-8 2.7-8 6 0 1.6.9 3 2.4 4.1" /><path d="M4 14v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" /><circle cx="16" cy="10" r="1" fill="currentColor" /><path d="M12 4c4.4 0 8 2.7 8 6" /></>,
    entrada: <><circle cx="12" cy="12" r="9" /><path d="M12 7v10M8 13l4 4 4-4" /></>,
    saida: <><circle cx="12" cy="12" r="9" /><path d="M12 17V7M16 11l-4-4-4 4" /></>,
    bank: <><path d="M3 10h18L12 3 3 10z" /><path d="M5 10v8M9 10v8M15 10v8M19 10v8M3 21h18" /></>,
    cal: <><rect x="4" y="5" width="16" height="16" rx="2" /><path d="M4 9h16M8 3v4M16 3v4" /></>,
    bill: <><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" /><path d="M9 8h6M9 12h6M9 16h3" /></>,
    list: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  };
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className={className}>
      {paths[name] || paths.list}
    </svg>
  );
}

function MdStat({ label, value, tone, icon }) {
  return (
    <div className={"md-stat is-" + tone}>
      <div className="md-stat-icon"><MdIcon name={icon} /></div>
      <div>
        <div className="md-stat-l">{label}</div>
        <div className="md-stat-v">{value}</div>
      </div>
    </div>
  );
}

function MdRow({ kind, title, tags, date, amount }) {
  return (
    <div className="md-row">
      <div className={"md-dot " + kind}></div>
      <div>
        <div className="md-title">{title}</div>
        <div className="md-tags">
          {tags.map((t, i) => (
            <span key={i} className={"md-tag " + (i > 0 ? "tag-2" : "")}>{t}</span>
          ))}
        </div>
      </div>
      <div className="md-amt-wrap">
        <div className="md-date">{date}</div>
        <div className={"md-amt " + kind}>{amount}</div>
      </div>
    </div>
  );
}

function MiniDash({ lang, t, currency, variant }) {
  const isPT = lang === "pt";
  const c = (n) => (currency === "BRL" ? "R$ " + n : "$ " + n);
  const lbl = t.dashboard.labels;
  const [tab, setTab] = React.useState(0);
  const [dataTab, setDataTab] = React.useState("date");
  const tabs = t.dashboard.tabs;

  const monthName = isPT ? "Maio/2026" : "May/2026";

  // Variant: hero = compact, full = section
  const compact = variant === "hero";

  // Income / expense rows
  const despesas = [
    { title: isPT ? "Compra na Shopee" : "Shopee purchase", tags: [isPT ? "RBV negócio" : "RBV business", isPT ? "Cartão Nubank" : "Nubank card"], date: "18/05", amount: c("172,82") },
    { title: isPT ? "Compra aprovada em JIM.COM* JOAO WILLIAM" : "Charge JIM.COM* JOAO WILLIAM", tags: [isPT ? "Outros" : "Other", isPT ? "Débito em Conta" : "Account debit"], date: "18/05", amount: c("6,09") },
    { title: isPT ? "Compra no Shopee" : "Shopee purchase", tags: [isPT ? "RBV negócio" : "RBV business", isPT ? "Cartão Nubank" : "Nubank card"], date: "18/05", amount: c("91,79") },
    { title: isPT ? "iFood · almoço" : "iFood · lunch", tags: [isPT ? "Alimentação" : "Food", isPT ? "Crédito Inter" : "Inter credit"], date: "17/05", amount: c("47,90") },
  ];
  const receitas = [
    { title: isPT ? "Aluguel AirBnb" : "AirBnb rent", tags: [isPT ? "Aluguel AirBnb" : "AirBnb rent", isPT ? "Depósito em Conta" : "Account deposit"], date: "16/05", amount: c("859,00") },
    { title: isPT ? "Salário" : "Salary", tags: [isPT ? "Salário" : "Salary", isPT ? "Depósito em Conta" : "Account deposit"], date: "15/05", amount: c("31.759,18") },
    { title: isPT ? "Aluguel Garagem" : "Garage rent", tags: [isPT ? "Outras Receitas" : "Other income", "PIX"], date: "15/05", amount: c("1.200,00") },
  ];

  // Budget tab data
  const budgets = [
    { cat: isPT ? "Mercado" : "Groceries", used: 1340, total: 1800 },
    { cat: isPT ? "Alimentação" : "Food / dining", used: 612, total: 600 },
    { cat: isPT ? "Transporte" : "Transport", used: 312, total: 400 },
    { cat: isPT ? "Lazer" : "Leisure", used: 178, total: 350 },
    { cat: isPT ? "Casa" : "Home", used: 950, total: 1100 },
    { cat: isPT ? "Saúde" : "Health", used: 90, total: 300 },
  ];

  // Card bills
  const bills = [
    { name: "Cartão Nubank", limit: 8500, used: 4380, due: "10/06", color: "#8a05be" },
    { name: "Cartão Inter", limit: 6000, used: 1842, due: "15/06", color: "#ff7a00" },
    { name: "Cartão C6", limit: 12000, used: 7320, due: "22/06", color: "#1a1a1a" },
  ];

  return (
    <div className="mini-dash">
      <div className="md-topbar">
        <div className="md-logo">
          <span style={{ width: 18, height: 18, borderRadius: "50%", background: "linear-gradient(135deg,#4a5bff,#7b3fe4)", display: "inline-block" }}></span>
          FinanIA
        </div>
        {!compact && (
          <nav>
            {tabs.map((label, i) => (
              <button key={i} className={i === tab ? "is-active" : ""} onClick={() => setTab(i)}>{label}</button>
            ))}
          </nav>
        )}
        <div className="md-user">
          <div className="md-avatar"></div>
          {!compact && <span>Orlei Barbosa</span>}
        </div>
      </div>

      <div className="md-hero">
        <div>
          <small>{isPT ? "Olá, Orlei Barbosa" : "Hi, Orlei Barbosa"}</small>
          <h3>{tabs[tab]} · {monthName}</h3>
        </div>
        <button>👁  {isPT ? "Ocultar" : "Hide"}</button>
      </div>

      {tab === 0 && (
        <>
          <div className="md-section-label">📅 {lbl.competencia}</div>
          <div className="md-stats">
            <MdStat label={lbl.receitas} value={c("34.034,18")} tone="pos" icon="receitas" />
            <MdStat label={lbl.despesas} value={c("38.497,73")} tone="neg" icon="despesas" />
            <MdStat label={lbl.saldo} value={c("-4.463,55")} tone="warn" icon="saldo" />
          </div>

          {!compact && (
            <>
              <div className="md-section-label">💰 {lbl.fluxo}</div>
              <div className="md-stats">
                <MdStat label={lbl.entradas} value={c("34.034,18")} tone="info" icon="entrada" />
                <MdStat label={lbl.saidas} value={c("25.924,24")} tone="neg" icon="saida" />
                <MdStat label={lbl.caixa} value={c("8.109,94")} tone="info" icon="bank" />
              </div>

              <div className="md-section-label">≡ {lbl.ultimas}</div>
              <div className="md-twocol">
                <div className="md-list">
                  <div className="md-list-h is-neg">
                    <span>● {lbl.ultDespesas}</span>
                    <div className="md-tabs">
                      <button className={dataTab === "date" ? "is-active" : ""} onClick={() => setDataTab("date")}>{isPT ? "Por Data" : "By date"}</button>
                      <button className={dataTab === "reg" ? "is-active" : ""} onClick={() => setDataTab("reg")}>{isPT ? "Por Registro" : "By entry"}</button>
                    </div>
                  </div>
                  {despesas.slice(0, 3).map((r, i) => (
                    <MdRow key={i} kind="neg" {...r} />
                  ))}
                </div>
                <div className="md-list">
                  <div className="md-list-h is-pos">
                    <span>● {lbl.ultReceitas}</span>
                    <div className="md-tabs">
                      <button className={dataTab === "date" ? "is-active" : ""} onClick={() => setDataTab("date")}>{isPT ? "Por Data" : "By date"}</button>
                      <button className={dataTab === "reg" ? "is-active" : ""} onClick={() => setDataTab("reg")}>{isPT ? "Por Registro" : "By entry"}</button>
                    </div>
                  </div>
                  {receitas.map((r, i) => (
                    <MdRow key={i} kind="pos" {...r} />
                  ))}
                </div>
              </div>
            </>
          )}

          {compact && (
            <div className="md-twocol" style={{ paddingTop: 6 }}>
              <div className="md-list">
                <div className="md-list-h is-neg">
                  <span>● {lbl.ultDespesas}</span>
                </div>
                {despesas.slice(0, 2).map((r, i) => (
                  <MdRow key={i} kind="neg" {...r} />
                ))}
              </div>
              <div className="md-list">
                <div className="md-list-h is-pos">
                  <span>● {lbl.ultReceitas}</span>
                </div>
                {receitas.slice(0, 2).map((r, i) => (
                  <MdRow key={i} kind="pos" {...r} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {tab === 1 && (
        <>
          <div className="md-section-label">📅 {lbl.despesas}</div>
          <div className="md-stats">
            <MdStat label={isPT ? "No mês" : "This month"} value={c("38.497,73")} tone="neg" icon="despesas" />
            <MdStat label={isPT ? "Cartão de crédito" : "Credit card"} value={c("13.542,00")} tone="warn" icon="bill" />
            <MdStat label={isPT ? "Débito em conta" : "Account debit"} value={c("24.955,73")} tone="info" icon="bank" />
          </div>
          <div className="md-section-label">≡ {lbl.ultDespesas}</div>
          <div className="md-twocol" style={{ gridTemplateColumns: "1fr" }}>
            <div className="md-list">
              {despesas.map((r, i) => (
                <MdRow key={i} kind="neg" {...r} />
              ))}
            </div>
          </div>
        </>
      )}

      {tab === 2 && (
        <>
          <div className="md-section-label">💳 {lbl.fatura}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, padding: "0 22px 22px" }}>
            {bills.map((b, i) => {
              const pct = Math.round((b.used / b.limit) * 100);
              return (
                <div key={i} style={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 12, padding: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>{b.name}</div>
                    <div style={{ width: 28, height: 18, borderRadius: 3, background: b.color }}></div>
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 22, color: "var(--ink-1)", letterSpacing: "-0.02em" }}>
                    {c(b.used.toLocaleString(isPT ? "pt-BR" : "en-US"))}
                  </div>
                  <div style={{ fontSize: 11.5, color: "var(--ink-3)", marginBottom: 10 }}>
                    {isPT ? "de" : "of"} {c(b.limit.toLocaleString(isPT ? "pt-BR" : "en-US"))} · {isPT ? "vence" : "due"} {b.due}
                  </div>
                  <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: pct + "%", background: pct > 80 ? "var(--neg)" : "var(--brand-grad)", borderRadius: 4 }}></div>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 6 }}>{pct}% {isPT ? "usado" : "used"}</div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {tab === 3 && (
        <>
          <div className="md-section-label">🎯 {lbl.budget}</div>
          <div style={{ display: "grid", gap: 8, padding: "0 22px 22px" }}>
            {budgets.map((b, i) => {
              const pct = Math.min(100, Math.round((b.used / b.total) * 100));
              const over = b.used > b.total;
              return (
                <div key={i} style={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 10, padding: "12px 14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: 13.5 }}>{b.cat}</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, color: over ? "var(--neg)" : "var(--ink-2)", fontWeight: 600 }}>
                      {c(b.used.toLocaleString(isPT ? "pt-BR" : "en-US"))} / {c(b.total.toLocaleString(isPT ? "pt-BR" : "en-US"))}
                    </div>
                  </div>
                  <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: pct + "%", background: over ? "var(--neg)" : (pct > 75 ? "var(--warn)" : "var(--pos)"), borderRadius: 4 }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

Object.assign(window, { MiniDash, MdIcon });
