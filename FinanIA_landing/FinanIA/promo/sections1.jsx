// FinanIA Promo — shared helpers + sections 1 (nav, hero, stats, situations, comparison, cycle).

// ── Scroll reveal hook (scroll-position based; robust) ──
function useReveal() {
  React.useEffect(() => {
    let raf = 0;
    const run = () => {
      const h = window.innerHeight || document.documentElement.clientHeight;
      document.querySelectorAll(".reveal:not(.in)").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.top < h * 0.92 && r.bottom > 0) el.classList.add("in");
      });
    };
    const onScroll = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(run); };
    // initial passes (cover late layout/font/image shifts)
    run();
    requestAnimationFrame(run);
    const t1 = setTimeout(run, 250);
    const t2 = setTimeout(run, 800);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    window.addEventListener("load", run);
    return () => {
      cancelAnimationFrame(raf); clearTimeout(t1); clearTimeout(t2);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.removeEventListener("load", run);
    };
  }, []);
}

// ── Image placeholder (user fills by swapping file / dropping image) ──
function Ph({ label, dark }) {
  return (
    <div className={"ph" + (dark ? " ph-dark" : "")}>
      <span className="ph-label">{label}</span>
    </div>
  );
}

// ── HTML helper ──
function H({ html, as = "span", className }) {
  const Tag = as;
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}

// ── Icons ──
function Icon({ n }) {
  const p = {
    bank: <><path d="M3 10h18L12 3 3 10z"/><path d="M5 10v8M9 10v8M15 10v8M19 10v8M3 21h18"/></>,
    sheet: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 3v18"/></>,
    apps: <><rect x="4" y="4" width="6" height="6" rx="1.5"/><rect x="14" y="4" width="6" height="6" rx="1.5"/><rect x="4" y="14" width="6" height="6" rx="1.5"/><rect x="14" y="14" width="6" height="6" rx="1.5"/></>,
    app: <><rect x="6" y="3" width="12" height="18" rx="3"/><path d="M11 18h2"/></>,
    ai: <><path d="M12 3l1.8 4.6L18 9.4l-4.2 1.8L12 16l-1.8-4.8L6 9.4l4.2-1.8z"/><circle cx="18" cy="5" r="1.4" fill="currentColor"/></>,
    device: <><rect x="3" y="4" width="14" height="11" rx="2"/><path d="M3 18h14M17 9h4v9a2 2 0 0 1-2 2h-2"/></>,
    lock: <><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></>,
    cam: <><path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="3.5"/></>,
    mic: <><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></>,
    txt: <><path d="M4 5h16M4 10h16M4 15h10"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></>,
    bell: <><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6z"/><path d="M10 20a2 2 0 0 0 4 0"/></>,
    alert: <><path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17v.5"/></>,
    bill: <><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h5"/></>,
  };
  return <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{p[n] || p.apps}</svg>;
}

const U = () => window.PROMO.urls;

// ═══════════════ DEVICE MOCKUP (laptop + phone, wraps real screenshots) ═══════════════
function DeviceMock({ laptopImg, phoneImg, alt, dark }) {
  return (
    <div className={"mock-stage" + (dark ? " mock-dark" : "")}>
      <div className="mock-laptop">
        <div className="screen"><img src={laptopImg} alt={alt || "FinanIA"} /></div>
        <div className="base"></div>
      </div>
      {phoneImg ? (
        <div className="mock-phone"><img src={phoneImg} alt="" /></div>
      ) : null}
    </div>
  );
}

// ═══════════════ URGENCY + NAV ═══════════════
function Urgency() {
  const d = window.PROMO.urgency;
  return (
    <div className="urgency">
      <span>🔥 {d.text} · <b>{d.strong}</b></span>
      <span className="pill">{d.pill}</span>
    </div>
  );
}

function Nav() {
  const [scrolled, setScrolled] = React.useState(false);
  const d = window.PROMO.nav;
  React.useEffect(() => {
    const f = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", f); return () => window.removeEventListener("scroll", f);
  }, []);
  return (
    <header className="nav" data-scrolled={scrolled}>
      <div className="container nav-inner">
        <a href={U().ajuda} className="nav-logo"><img src="logo-finan.svg" alt="FiNan" /></a>
        <div className="nav-right">
          <a href={U().login} className="btn btn-ghost nav-cta nav-login">{d.login}</a>
          <a href={U().assinar} className="btn btn-primary nav-cta">{d.cta}</a>
        </div>
      </div>
    </header>
  );
}

// ═══════════════ PROMO VIDEO PLAYER ═══════════════
function PromoVideoPlayer() {
  const videos = (window.PROMO.hero.promoVideos || []);
  const [open, setOpen] = React.useState(false);
  const [active, setActive] = React.useState(0);
  const iframeRef = React.useRef(null);

  // Pause iframe when closing or switching — reload src without autoplay
  function stopCurrent() {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src.replace("&autoplay=1", "").replace("?autoplay=1", "?");
    }
  }

  function toggle() {
    if (open) stopCurrent();
    setOpen(o => !o);
  }

  function select(i) {
    if (i === active) return;
    stopCurrent();
    setActive(i);
  }

  const vid = videos[active];
  const embedBase = vid ? "https://www.youtube-nocookie.com/embed/" + vid.id + "?rel=0&playsinline=1&modestbranding=1" : "";

  return (
    <div className="promo-vp-wrap">
      {/* Trigger bar */}
      <button className="promo-vp-trigger" onClick={toggle} aria-expanded={open}>
        <span className="promo-vp-play-ic">▶</span>
        <span>Ver vídeo da oferta</span>
        <span className="promo-vp-chevron">{open ? "▲" : "▼"}</span>
      </button>

      {/* Suspended panel */}
      {open && (
        <div className="promo-vp-panel">
          {/* Main player */}
          <div className="promo-vp-main">
            <iframe
              ref={iframeRef}
              key={active}
              src={embedBase + "&autoplay=1"}
              allow="autoplay; fullscreen; picture-in-picture"
              allowFullScreen
              title={vid ? vid.title : ""}
            ></iframe>
          </div>
          {/* Scrollable playlist */}
          <div className="promo-vp-list">
            {videos.map((v, i) => (
              <button
                key={v.id}
                className={"promo-vp-item" + (i === active ? " active" : "")}
                onClick={() => select(i)}
              >
                <img
                  src={"https://i.ytimg.com/vi/" + v.id + "/mqdefault.jpg"}
                  alt={v.title}
                  className="promo-vp-thumb"
                />
                <span className="promo-vp-item-title">{v.title}</span>
                {i === active && <span className="promo-vp-now">▶</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════ HERO ═══════════════
function Hero() {
  const d = window.PROMO.hero;
  return (
    <section className="hero">
      <div className="container hero-grid">
        <div>
          <span className="hero-badge reveal"><span className="b-dot"><Icon n="ai" /></span>{d.badge}</span>
          <H as="h1" className="h1 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2">{d.sub}</p>
          <div className="hero-cta reveal d3">
            <a href={U().assinar} className="btn btn-primary btn-lg">{d.cta} →</a>
          </div>
          <p className="hero-price reveal d3"><H html={d.price} /></p>
          <div className="hero-chips reveal d4">
            {(d.chips || []).map((c, i) => <span key={i} className="hero-chip">✓ {c}</span>)}
          </div>
          <div className="hero-proof reveal d4">
            <span className="hero-avatars"><span></span><span></span><span></span><span></span></span>
            {d.proof}
          </div>
          <PromoVideoPlayer />
        </div>
        <div className="hero-visual reveal d2">
          <img className="hero-shot" src="hero-woman.png" alt="Profissional usando o FinanIA no celular" />
          <div className="float-card fc-1">
            <div className="fc-label">{d.fc1.label}</div>
            <div className="fc-value pos">{d.fc1.value}</div>
          </div>
          <div className="float-card fc-2" style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className="gauge"><span>{d.fc2.value}</span></div>
            <div style={{ maxWidth: 90 }}><div className="fc-label">{d.fc2.label}</div></div>
          </div>
          <div className="float-card fc-3">
            <div className="fc-label">Gastos por categoria</div>
            <div className="mini-bars">
              <span style={{ height: "64%" }}></span>
              <span style={{ height: "88%" }}></span>
              <span style={{ height: "42%" }}></span>
              <span style={{ height: "100%" }}></span>
              <span style={{ height: "55%" }}></span>
              <span style={{ height: "30%" }}></span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ STATS ═══════════════
function Stats() {
  return (
    <section className="stats">
      <div className="container stats-grid">
        {window.PROMO.stats.map((s, i) => (
          <div key={i} className={"stat reveal d" + (i + 1)}>
            <div className="n">{s.n}</div>
            <div className="l">{s.l}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ═══════════════ SITUATIONS ═══════════════
function Situations() {
  const d = window.PROMO.situations;
  return (
    <section className="section" id="para-quem">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">Para quem é</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
        </div>
        <div className="sit-grid">
          {d.items.map((s, i) => (
            <div key={i} className={"sit-card reveal d" + ((i % 3) + 1)}>
              <div className="sit-top">
                <span className="sit-ic"><Icon n={s.icon} /></span>
                <span className="sit-n">Situação {String(i + 1).padStart(2, "0")}</span>
              </div>
              <h4 className="sit-title">{s.title}</h4>
              <p className="sit-desc">{s.desc}</p>
              <div className="sit-sol"><span className="sit-check">✓</span>{s.sol}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════ COMPARISON (dark) ═══════════════
function Comparison() {
  const d = window.PROMO.comparison;
  return (
    <section className="section dark">
      <div className="container cmp-grid">
        <div>
          <H as="h2" className="h2 reveal" html={d.titleHtml} />
          <div style={{ marginTop: 22 }}>
            {d.body.map((p, i) => <p key={i} className="lead reveal d1" style={{ marginTop: 14 }}>{p}</p>)}
          </div>
          <a href={U().assinar} className="btn btn-primary btn-lg reveal d2" style={{ marginTop: 28 }}>{d.cta} →</a>
        </div>
        <div className="cmp-table reveal d1">
          <div className="cmp-row">
            <div className="cmp-head">Tentativas</div>
            {d.cols.map((c, i) => <div key={i} className="cmp-head">{c}</div>)}
          </div>
          {d.rows.map((r, i) => (
            <div key={i} className="cmp-row">
              <div className="cmp-name"><span className="ci"><Icon n={r.icon} /></span>{r.name}</div>
              {r.cells.map((c, j) => (
                <div key={j} className="cmp-cell"><span className={"tick " + (c ? "yes" : "no")}>{c ? "✓" : "✕"}</span></div>
              ))}
            </div>
          ))}
          <div className="cmp-row is-us">
            <div className="cmp-name"><span className="ci"><img src="logo-finan.svg" alt="" style={{ height: 16 }} /></span>{d.us.name}</div>
            {d.us.cells.map((c, j) => (
              <div key={j} className="cmp-cell"><span className="tick yes">✓</span></div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ CYCLE / METHOD ═══════════════
function Cycle() {
  const d = window.PROMO.cycle;
  return (
    <section className="section">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2">{d.sub}</p>
          <p className="reveal d2" style={{ marginTop: 18, fontWeight: 800, fontSize: 18 }}>
            <span className="mark">{d.quote}</span>
          </p>
        </div>
        <div className="cycle-steps">
          {d.steps.map((s, i) => (
            <div key={i} className={"cstep reveal d" + (i + 1)}>
              <div className="num">{String(i + 1).padStart(2, "0")}</div>
              <h4>{s.t}</h4>
              <p>{s.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { useReveal, Ph, H, Icon, U, DeviceMock, Urgency, Nav, Hero, Stats, Situations, Comparison, Cycle });
