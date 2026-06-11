// Main FinanIA landing app — orchestrates nav, hero, sections, tweaks.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "lang": "pt",
  "headlineStyle": "split",
  "showLogos": true
}/*EDITMODE-END*/;

function FinaniaLanding() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [scrolled, setScrolled] = React.useState(false);
  const [menuOpen, setMenuOpen] = React.useState(false);
  const lang = t.lang;
  const dict = window.I18N[lang];

  // Theme on documentElement
  React.useEffect(() => {
    document.documentElement.dataset.theme = t.theme === "light" ? "" : t.theme;
  }, [t.theme]);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const currency = lang === "pt" ? "BRL" : "USD";

  // Headline variants
  const renderHeadline = () => {
    if (t.headlineStyle === "single") {
      return (
        <h1>
          {dict.hero.title_a} <span className="grad">{dict.hero.title_b.replace(".", "")}</span>
        </h1>
      );
    }
    if (t.headlineStyle === "quiet") {
      return (
        <h1>
          {dict.hero.title_a} {dict.hero.title_b}
          <br />
          <span className="quiet">{dict.hero.title_c}</span>
        </h1>
      );
    }
    return (
      <h1>
        {dict.hero.title_a} <span className="grad">{dict.hero.title_b}</span>
        <br />
        <span className="quiet">{dict.hero.title_c}</span>
      </h1>
    );
  };

  return (
    <div>
      {/* NAV */}
      <header className="nav" data-scrolled={scrolled} data-screen-label="00 Nav">
        <div className="container nav-inner">
          <a href="#" className="nav-logo" onClick={() => setMenuOpen(false)}>
            <img src="logo-finan.svg" alt="FiNan" className="logo-img" />
          </a>
          <nav className="nav-links">
            <a href="#features">{dict.nav.features}</a>
            <a href="#dashboard">{dict.nav.product}</a>
            <a href="#pricing">{dict.nav.pricing}</a>
            <a href="#faq">{dict.nav.faq}</a>
          </nav>
          <div className="nav-right">
            <div className="lang-toggle" role="group" aria-label="Language">
              <button aria-pressed={lang === "pt"} onClick={() => setTweak("lang", "pt")}>PT</button>
              <button aria-pressed={lang === "en"} onClick={() => setTweak("lang", "en")}>EN</button>
            </div>
            <a href="https://finania.pro" target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">{dict.nav.login}</a>
            <a href="https://finania.pro/assinatura/assine-agora" target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">{dict.nav.cta}</a>
          </div>
          <button
            className={"nav-hamburger" + (menuOpen ? " is-open" : "")}
            aria-label="Menu"
            onClick={() => setMenuOpen(o => !o)}
          >
            <span /><span /><span />
          </button>
        </div>
        <div className={"nav-mobile-menu" + (menuOpen ? " is-open" : "")}>
          <a href="#features" onClick={() => setMenuOpen(false)}>{dict.nav.features}</a>
          <a href="#dashboard" onClick={() => setMenuOpen(false)}>{dict.nav.product}</a>
          <a href="#pricing" onClick={() => setMenuOpen(false)}>{dict.nav.pricing}</a>
          <a href="#faq" onClick={() => setMenuOpen(false)}>{dict.nav.faq}</a>
          <div className="nav-mobile-cta">
            <a href="https://finania.pro" target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">{dict.nav.login}</a>
            <a href="https://finania.pro/assinatura/assine-agora" target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">{dict.nav.cta}</a>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="hero" data-screen-label="01 Hero">
        <div className="container hero-grid">
          <div style={{ textAlign: "center", maxWidth: 880, margin: "0 auto", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span className="hero-eyebrow">
              <span className="dot">✦</span>
              {dict.badge}
            </span>
            {renderHeadline()}
            <p className="hero-sub" style={{ marginInline: "auto" }}>{dict.hero.sub}</p>
            <div className="hero-cta">
              <a href="https://finania.pro/assinatura/assine-agora" target="_blank" rel="noopener noreferrer" className="btn btn-primary">{dict.hero.cta_primary} <span>→</span></a>
              <a href="#dashboard" className="btn btn-ghost">▶ {dict.hero.cta_secondary}</a>
            </div>
            <div className="hero-note">{dict.hero.cta_note}</div>
          </div>

          <div className="hero-visual">
            <div className="hero-shadow"></div>
            <div className="dash-card">
              <img src="dashboard-real.png" alt="FinanIA Dashboard" style={{ width: '100%', display: 'block' }} />
            </div>
          </div>
        </div>
      </section>

      {/* LOGOS */}
      {t.showLogos && (
        <section className="logos" data-screen-label="02 Logos">
          <div className="container logos-inner">
            <div className="logos-kicker">{dict.proof.kicker}</div>
            {dict.proof.logos.map((name, i) => (
              <div key={i} className="logo-mark">
                <span className="logo-glyph">{name.charAt(0)}</span>
                {name}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* PAIN */}
      <section className="section" id="problem" data-screen-label="03 Problema">
        <div className="container pain-grid">
          <div>
            <span className="kicker">{dict.pain.kicker}</span>
            <h2 className="h-section">{dict.pain.title}</h2>
            <p className="lead">{dict.pain.sub}</p>
            <div className="pain-quote">{dict.pain.quote}</div>
          </div>
          <div className="pain-bullets">
            {dict.pain.bullets.map((b, i) => (
              <div key={i} className="pain-b">
                <div className="pain-n">0{i + 1}</div>
                <div>
                  <h4>{b.t}</h4>
                  <p>{b.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section" id="features" data-screen-label="04 Recursos" style={{ background: "var(--bg-soft)" }}>
        <div className="container">
          <div className="features-head">
            <div>
              <span className="kicker">{dict.features.kicker}</span>
              <h2 className="h-section">{dict.features.title}</h2>
            </div>
            <p className="lead">{dict.features.sub}</p>
          </div>
          <div className="features-grid">
            {dict.features.items.map((f, i) => (
              <div key={i} className="feat">
                <div className="feat-tag">{f.tag}</div>
                <h4>{f.t}</h4>
                <p>{f.d}</p>
                {i === 0 && <FeatIllus kind="budget" />}
                {i === 1 && <FeatIllus kind="card" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHATSAPP DEMO */}
      <section className="section" id="whatsapp" data-screen-label="05 WhatsApp">
        <div className="container demo-split">
          <div>
            <span className="kicker">{dict.whatsapp.kicker}</span>
            <h2 className="h-section">{dict.whatsapp.title}</h2>
            <p className="lead">{dict.whatsapp.sub}</p>
            <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                { ic: "📷", t: lang === "pt" ? "Foto do recibo → OCR e classificação" : "Receipt photo → OCR + categorization" },
                { ic: "🎙", t: lang === "pt" ? "Áudio com a despesa → transcrito e lançado" : "Voice note → transcribed and logged" },
                { ic: "💬", t: lang === "pt" ? "Texto livre: “gastei 47 no Uber”" : "Free text: “spent 47 on Uber”" },
                { ic: "📊", t: lang === "pt" ? "Pergunta de saldo, orçamento ou tendência" : "Ask about balance, budget or trend" },
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 14, alignItems: "center" }}>
                  <span style={{ width: 36, height: 36, borderRadius: 10, background: "var(--surface-2)", display: "grid", placeItems: "center", fontSize: 18 }}>{item.ic}</span>
                  <span style={{ fontSize: 15.5, color: "var(--ink-2)" }}>{item.t}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <WhatsAppDemo t={dict} lang={lang} />
          </div>
        </div>
      </section>

      {/* DASHBOARD DEMO */}
      <section className="section" id="dashboard" data-screen-label="06 Dashboard" style={{ background: "var(--bg-soft)" }}>
        <div className="container">
          <div style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 48px", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span className="kicker">{dict.dashboard.kicker}</span>
            <h2 className="h-section">{dict.dashboard.title}</h2>
            <p className="lead" style={{ marginInline: "auto" }}>{dict.dashboard.sub}</p>
          </div>
          <div className="dash-card">
            <img src="dashboard-real.png" alt="FinanIA Dashboard" style={{ width: '100%', display: 'block' }} />
          </div>
          {/* Chart — Balanço Mensal */}
          <div className="report-intro" style={{ marginTop: 56, marginBottom: 20, textAlign: 'center', maxWidth: 680, marginInline: 'auto' }}>
            <h3 style={{ fontSize: 'clamp(22px, 3vw, 32px)', fontWeight: 700, letterSpacing: '-0.015em', color: 'var(--ink-1)', margin: '0 0 10px' }}>
              {lang === 'pt' ? 'Saiba exatamente pra onde seu dinheiro foi' : 'Know exactly where your money went'}
            </h3>
            <p style={{ fontSize: 16, color: 'var(--ink-2)', margin: 0, textWrap: 'pretty' }}>
              {lang === 'pt'
                ? 'O relatório de Balanço Mensal compara receitas e despesas mês a mês. Sem ele, você só descobre que gastou demais quando já é tarde. Com ele, você vê a tendência antes que ela vire problema.'
                : 'The Monthly Balance report compares income and expenses month by month. Without it, you only realize you overspent when it\'s too late. With it, you spot the trend before it becomes a problem.'}
            </p>
          </div>
          <div className="dash-card">
            <img src="chart-balanco.png" alt={lang === 'pt' ? 'Balanço Mensal — Receitas vs Despesas' : 'Monthly Balance — Income vs Expenses'} style={{ width: '100%', display: 'block' }} />
          </div>

          {/* Fluxo de Caixa */}
          <div className="report-intro" style={{ marginTop: 56, marginBottom: 20, textAlign: 'center', maxWidth: 680, marginInline: 'auto' }}>
            <h3 style={{ fontSize: 'clamp(22px, 3vw, 32px)', fontWeight: 700, letterSpacing: '-0.015em', color: 'var(--ink-1)', margin: '0 0 10px' }}>
              {lang === 'pt' ? 'Dinheiro que entra, dinheiro que sai — tudo visível' : 'Money in, money out — all visible'}
            </h3>
            <p style={{ fontSize: 16, color: 'var(--ink-2)', margin: 0, textWrap: 'pretty' }}>
              {lang === 'pt'
                ? 'O Fluxo de Caixa mostra o saldo real da sua conta, não só o que você registrou. Entradas, saídas e o que sobrou — mês a mês, sem surpresa. É o relatório que separa quem controla de quem adivinha.'
                : 'Cash Flow shows the real balance of your account, not just what you logged. Money in, money out, and what\'s left — month by month, no surprises. It\'s the report that separates those who control from those who guess.'}
            </p>
          </div>
          <div className="dash-card">
            <img src="fluxo-caixa.png" alt={lang === 'pt' ? 'Fluxo de Caixa' : 'Cash Flow'} style={{ width: '100%', display: 'block' }} />
          </div>

          {/* Previsão de Faturas */}
          <div className="report-intro" style={{ marginTop: 56, marginBottom: 20, textAlign: 'center', maxWidth: 680, marginInline: 'auto' }}>
            <h3 style={{ fontSize: 'clamp(22px, 3vw, 32px)', fontWeight: 700, letterSpacing: '-0.015em', color: 'var(--ink-1)', margin: '0 0 10px' }}>
              {lang === 'pt' ? 'Nunca mais seja surpreendido pela fatura do cartão' : 'Never be surprised by your credit card bill again'}
            </h3>
            <p style={{ fontSize: 16, color: 'var(--ink-2)', margin: 0, textWrap: 'pretty' }}>
              {lang === 'pt'
                ? 'A Previsão de Faturas projeta o valor de cada cartão nos próximos meses. Você vê o que vai pagar antes de chegar a cobrança. Chega de abrir a fatura e levar um susto — aqui você planeja, não reage.'
                : 'Bill Forecast projects each card\'s amount for the coming months. You see what you\'ll pay before the bill arrives. No more opening a statement in shock — here you plan, not react.'}
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div className="dash-card">
              <img src="previsao-faturas.png" alt={lang === 'pt' ? 'Previsão de Faturas — Resumo Global' : 'Bill Forecast — Global Summary'} style={{ width: '100%', display: 'block' }} />
            </div>
            <div className="dash-card">
              <img src="previsao-cartoes.png" alt={lang === 'pt' ? 'Previsão de Faturas — Por Cartão' : 'Bill Forecast — Per Card'} style={{ width: '100%', display: 'block' }} />
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="section" id="testimonials" data-screen-label="07 Depoimentos">
        <div className="container">
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
            <span className="kicker">{dict.testimonials.kicker}</span>
            <h2 className="h-section" style={{ maxWidth: 760 }}>{dict.testimonials.title}</h2>
          </div>
          <div className="testi-grid">
            {dict.testimonials.items.map((tt, i) => (
              <div key={i} className="testi">
                <div>
                  <span className="testi-mark">“</span>
                  <div className="testi-q">{tt.quote}</div>
                </div>
                <div className="testi-who">
                  <div className="testi-avatar">{tt.name.charAt(0)}</div>
                  <div>
                    <div className="testi-name">{tt.name}</div>
                    <div className="testi-role">{tt.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section className="section" id="pricing" data-screen-label="08 Planos" style={{ background: "var(--bg-soft)" }}>
        <div className="container">
          <Pricing t={dict} lang={lang} />
        </div>
      </section>

      {/* FAQ */}
      <section className="section" id="faq" data-screen-label="09 FAQ">
        <div className="container faq-grid">
          <div>
            <span className="kicker">{dict.faq.kicker}</span>
            <h2 className="h-section">{dict.faq.title}</h2>
          </div>
          <FAQ t={dict} />
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="final" data-screen-label="10 CTA Final">
        <div className="container">
          <div className="final-card">
            <span className="kicker" style={{ color: "color-mix(in oklch, var(--bg) 60%, var(--ink-3))" }}>{dict.finalCta.kicker}</span>
            <h2>{dict.finalCta.title}</h2>
            <p>{dict.finalCta.sub}</p>
            <a href="https://finania.pro/assinatura/assine-agora" target="_blank" rel="noopener noreferrer" className="btn btn-primary">{dict.finalCta.cta} <span>→</span></a>
            <div className="final-note">{dict.finalCta.note}</div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer" data-screen-label="11 Footer">
        <div className="container footer-grid">
          <div>
            <a href="https://finania.pro" target="_blank" rel="noopener noreferrer" className="nav-logo">
              <img src="logo-finan.svg" alt="FiNan" className="logo-img" />
            </a>
            <p className="footer-tag">{dict.footer.tagline}</p>
          </div>
          <div>
            <h5>{dict.footer.product}</h5>
            <ul>{dict.footer.productLinks.map((l, i) => <li key={i}><a href="#">{l}</a></li>)}</ul>
          </div>
          <div>
            <h5>{dict.footer.company}</h5>
            <ul>{dict.footer.companyLinks.map((l, i) => <li key={i}><a href="#">{l}</a></li>)}</ul>
          </div>
          <div>
            <h5>{dict.footer.legal}</h5>
            <ul>{dict.footer.legalLinks.map((l, i) => <li key={i}><a href="/compliance/">{l}</a></li>)}</ul>
          </div>
        </div>
        <div className="container">
          <div className="footer-bottom">
            <span>{dict.footer.copy}</span>
            <span style={{ display: "flex", gap: 14 }}>
              <a href="https://finania.pro" target="_blank" rel="noopener noreferrer">{lang === "pt" ? "Entrar" : "Log in"}</a>
              <a href="https://finania.pro/assinatura/assine-agora" target="_blank" rel="noopener noreferrer">{lang === "pt" ? "Criar conta Free" : "Create free account"}</a>
              <a href="https://finania.pro/ajuda" target="_blank" rel="noopener noreferrer">{lang === "pt" ? "Ajuda" : "Help"}</a>
            </span>
          </div>
        </div>
      </footer>

      {/* TWEAKS PANEL */}
      <TweaksPanel>
        <TweakSection label={lang === "pt" ? "Idioma" : "Language"} />
        <TweakRadio
          label={lang === "pt" ? "Idioma" : "Language"}
          value={lang}
          options={["pt", "en"]}
          onChange={(v) => setTweak("lang", v)}
        />

        <TweakSection label={lang === "pt" ? "Tema" : "Theme"} />
        <TweakSelect
          label={lang === "pt" ? "Paleta" : "Palette"}
          value={t.theme}
          options={[
            { value: "light", label: lang === "pt" ? "Padrão (índigo claro)" : "Default (light indigo)" },
            { value: "dark", label: lang === "pt" ? "Dark neon" : "Dark neon" },
            { value: "lime", label: lang === "pt" ? "Verde lima" : "Lime green" },
            { value: "editorial", label: lang === "pt" ? "Editorial creme" : "Editorial cream" },
          ]}
          onChange={(v) => setTweak("theme", v)}
        />

        <TweakSection label={lang === "pt" ? "Conteúdo" : "Content"} />
        <TweakSelect
          label={lang === "pt" ? "Estilo da headline" : "Headline style"}
          value={t.headlineStyle}
          options={[
            { value: "split", label: lang === "pt" ? "Dividida + gradiente" : "Split + gradient" },
            { value: "quiet", label: lang === "pt" ? "Sóbria, sem gradiente" : "Quiet, no gradient" },
            { value: "single", label: lang === "pt" ? "Curta, 1 linha" : "Short, 1 line" },
          ]}
          onChange={(v) => setTweak("headlineStyle", v)}
        />
        <TweakToggle
          label={lang === "pt" ? "Mostrar logos de prova" : "Show proof logos"}
          value={t.showLogos}
          onChange={(v) => setTweak("showLogos", v)}
        />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<FinaniaLanding />);
