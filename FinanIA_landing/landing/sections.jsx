// WhatsApp interactive demo + section components.

function WhatsAppDemo({ t, lang }) {
  const isPT = lang === "pt";
  const baseChat = t.whatsapp.chat;
  const [visible, setVisible] = React.useState([]);
  const [typing, setTyping] = React.useState(false);
  const [input, setInput] = React.useState("");
  const bodyRef = React.useRef(null);

  // Replay loop on mount / language change
  React.useEffect(() => {
    setVisible([]);
    setTyping(false);
    let cancelled = false;
    let timers = [];

    const play = async () => {
      for (let i = 0; i < baseChat.length; i++) {
        if (cancelled) return;
        const msg = baseChat[i];
        if (msg.side === "in") {
          setTyping(true);
          await new Promise((r) => timers.push(setTimeout(r, 900)));
          if (cancelled) return;
          setTyping(false);
        } else {
          await new Promise((r) => timers.push(setTimeout(r, 400)));
        }
        if (cancelled) return;
        setVisible((v) => [...v, { ...msg, time: nowTime(i) }]);
        await new Promise((r) => timers.push(setTimeout(r, 600)));
      }
      // pause then loop
      await new Promise((r) => timers.push(setTimeout(r, 4500)));
      if (cancelled) return;
      setVisible([]);
      play();
    };

    play();
    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
    };
  }, [lang]);

  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [visible, typing]);

  return (
    <div className="wa">
      <div className="wa-screen">
        <div className="wa-head">
          <div className="wa-avatar">F</div>
          <div>
            <div className="wa-name">FinanIA · {isPT ? "Agente" : "Agent"}</div>
            <div className="wa-status">{isPT ? "online · responde em segundos" : "online · replies in seconds"}</div>
          </div>
        </div>
        <div className="wa-body" ref={bodyRef}>
          {visible.map((m, i) => (
            <div key={i} className={"wa-msg " + m.side}>
              {m.text}
              <span className="wa-time">{m.time}</span>
            </div>
          ))}
          {typing && (
            <div className="wa-typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}
        </div>
        <div className="wa-input">
          <div className="wa-field">{input || t.whatsapp.reply_placeholder}</div>
          <div className="wa-send">↑</div>
        </div>
      </div>
    </div>
  );
}

function nowTime(seed) {
  const base = new Date();
  base.setMinutes(base.getMinutes() - (10 - seed));
  return base.toTimeString().slice(0, 5);
}

/* ─────────────── FAQ ─────────────── */
function FAQ({ t }) {
  const [open, setOpen] = React.useState(0);
  return (
    <div className="faq-list">
      {t.faq.items.map((item, i) => (
        <div key={i} className={"faq-item " + (open === i ? "is-open" : "")}>
          <button className="faq-q" onClick={() => setOpen(open === i ? -1 : i)}>
            <span>{item.q}</span>
            <span className="faq-i">+</span>
          </button>
          <div className="faq-a">{item.a}</div>
        </div>
      ))}
    </div>
  );
}

/* ─────────────── Pricing ─────────────── */
function Pricing({ t, lang }) {
  const [yearly, setYearly] = React.useState(false);

  const ctaColors = {
    dark: { bg: "var(--ink-1)", color: "var(--bg)" },
    green: { bg: "#16a47a", color: "#fff" },
    brand: { bg: "var(--brand-grad)", color: "#fff" },
    orange: { bg: "#f4a833", color: "#fff" },
    teal: { bg: "#0ea5e9", color: "#fff" },
  };

  return (
    <>
      <div className="pricing-head">
        <span className="kicker">{t.pricing.kicker}</span>
        <h2 className="h-section" style={{ textAlign: "center" }}>{t.pricing.title}</h2>
        <p className="lead" style={{ textAlign: "center" }}>{t.pricing.sub}</p>
        <div className="pricing-toggle">
          <button aria-pressed={!yearly} onClick={() => setYearly(false)}>{t.pricing.monthly}</button>
          <button aria-pressed={yearly} onClick={() => setYearly(true)}>
            {t.pricing.yearly}
            <span className="save">{t.pricing.save}</span>
          </button>
        </div>
      </div>

      {/* Mercado Pago badge */}
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontSize: 12.5, color: "var(--ink-3)",
          background: "var(--surface)", border: "1px solid var(--line)",
          borderRadius: 999, padding: "6px 14px"
        }}>
          🔒 {t.pricing.paymentNote.split("·")[0].trim()}
        </span>
      </div>

      {/* 5-plan grid */}
      <div className="plans plans-5">
        {t.pricing.plans.map((p, i) => {
          const price = yearly ? p.priceYearly : p.price;
          const unit = yearly ? p.unitYearly : p.unit;
          const cs = ctaColors[p.ctaStyle] || ctaColors.dark;
          return (
            <div key={i} className={"plan " + (p.highlight ? "is-highlight" : "")}>
              {p.tag && <div className="plan-tag">{p.tag}</div>}
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 28, marginBottom: 6 }}>{p.icon}</div>
                <div className="plan-name">{p.name}</div>
                <div className="plan-desc">{p.desc}</div>
              </div>
              <div className="plan-price-row" style={{ justifyContent: "center" }}>
                <span className="plan-price" style={{ fontFamily: "var(--font-mono)", fontSize: p.price === "Grátis" || p.price === "Free" ? 32 : undefined }}>{price}</span>
                <span className="plan-unit">{unit}</span>
              </div>
              <div className="plan-feats">
                {(p.features || []).map((f, j) => (
                  <div key={j} className="plan-feat">
                    <span className="plan-feat-check" style={{ background: "var(--pos-soft)", color: "var(--pos)" }}>✓</span>
                    <span>{f}</span>
                  </div>
                ))}
                {(p.negatives || []).map((f, j) => (
                  <div key={"n" + j} className="plan-feat plan-feat-neg">
                    <span className="plan-feat-check" style={{ background: "var(--neg-soft)", color: "var(--neg)" }}>✗</span>
                    <span style={{ color: "var(--ink-3)" }}>{f}</span>
                  </div>
                ))}
              </div>
              <a href={p.url} target="_blank" rel="noopener noreferrer"
                className="btn btn-plan-cta"
                style={{ background: cs.bg, color: cs.color, width: "100%", justifyContent: "center", marginTop: "auto", boxShadow: "none", border: 0 }}>
                {p.cta}
              </a>
            </div>
          );
        })}
      </div>

      {/* Comparison table */}
      {t.pricing.comparison && (
        <div style={{ marginTop: 64 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 24 }}>
            <span style={{ fontSize: 16 }}>📊</span>
            <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--ink-3)" }}>
              {t.pricing.compTitle}
            </span>
          </div>
          <div className="comp-table-wrap">
            <table className="comp-table">
              <thead>
                <tr>
                  {t.pricing.comparison.headers.map((h, i) => (
                    <th key={i} className={i === 0 ? "comp-label" : "comp-plan-col"}>
                      <span style={{ color: i === 3 ? "var(--brand-2)" : undefined, fontWeight: i === 3 ? 800 : undefined }}>{h}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {t.pricing.comparison.rows.map((row, ri) => {
                  const isPrice = ri >= t.pricing.comparison.rows.length - 2;
                  return (
                    <tr key={ri} className={isPrice ? "comp-price-row" : ""}>
                      <td className="comp-label">
                        {row.label}
                        {ri === t.pricing.comparison.rows.length - 1 && (
                          <span className="save" style={{ marginLeft: 6, fontSize: 10 }}>{t.pricing.save}</span>
                        )}
                      </td>
                      {row.values.map((v, vi) => {
                        let cls = "";
                        let displayVal = v;
                        if (v === "✓" || v === "∞") cls = "comp-yes";
                        else if (v === "✗") cls = "comp-no";
                        else if (v === "—") cls = "comp-dash";

                        if (v === "∞") displayVal = <span style={{ fontSize: 18 }}>∞</span>;
                        else if (v === "✓") displayVal = <span className="comp-dot comp-dot-yes">✓</span>;
                        else if (v === "✗") displayVal = <span className="comp-dot comp-dot-no">✗</span>;

                        return (
                          <td key={vi} className={"comp-val " + cls}>
                            {displayVal}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Payment note */}
      <div style={{ textAlign: "center", marginTop: 28, fontSize: 12.5, color: "var(--ink-3)", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
        <span>🔒</span>
        {t.pricing.paymentNote}
      </div>
    </>
  );
}

/* ─────────────── Feature card illustrations ─────────────── */
function FeatIllus({ kind }) {
  if (kind === "budget") {
    return (
      <div style={{ display: "grid", gap: 8, marginTop: 18 }}>
        {[
          { l: "Mercado", v: 74 },
          { l: "Transporte", v: 78 },
          { l: "Lazer", v: 51 },
        ].map((b, i) => (
          <div key={i}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--ink-3)", marginBottom: 4, fontWeight: 600 }}>
              <span>{b.l}</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>{b.v}%</span>
            </div>
            <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ height: "100%", width: b.v + "%", background: b.v > 75 ? "var(--warn)" : "var(--pos)", borderRadius: 4 }}></div>
            </div>
          </div>
        ))}
      </div>
    );
  }
  if (kind === "card") {
    return (
      <div style={{ display: "flex", gap: 8, marginTop: 18 }}>
        {[
          { c: "#8a05be", t: "Nubank" },
          { c: "#ff7a00", t: "Inter" },
          { c: "#111", t: "C6" },
        ].map((c, i) => (
          <div key={i} style={{ flex: 1, background: c.c, borderRadius: 8, padding: "12px 10px", color: "#fff", fontSize: 11, fontWeight: 600 }}>
            {c.t}
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, marginTop: 6 }}>R$ {(1000 + i * 1200).toLocaleString("pt-BR")}</div>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

Object.assign(window, { WhatsAppDemo, FAQ, Pricing, FeatIllus });
