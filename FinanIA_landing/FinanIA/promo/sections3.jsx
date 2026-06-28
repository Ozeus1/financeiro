// FinanIA Promo — sections 3 (testimonials + VIDEO SLOTS, story, bonus, offer, guarantee, faq, final cta, footer).

// ── Editable video slot: user pastes YouTube/Vimeo/MP4 URL; persists in localStorage ──
function toEmbed(url) {
  if (!url) return null;
  try {
    const u = url.trim();
    let m;
    if ((m = u.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([\w-]{6,})/))) {
      return { type: "iframe", src: "https://www.youtube-nocookie.com/embed/" + m[1] + "?rel=0&playsinline=1", thumb: "https://i.ytimg.com/vi/" + m[1] + "/hqdefault.jpg", watch: "https://youtu.be/" + m[1] };
    }
    if ((m = u.match(/vimeo\.com\/(?:video\/)?(\d+)/))) {
      return { type: "iframe", src: "https://player.vimeo.com/video/" + m[1] };
    }
    if (/\.(mp4|webm|mov|m4v)(\?.*)?$/i.test(u)) return { type: "video", src: u };
    if (/^https?:\/\//i.test(u)) return { type: "iframe", src: u };
  } catch (e) {}
  return null;
}

function VideoSlot({ url, quote, name }) {
  const [playing, setPlaying] = React.useState(false);
  const embed = toEmbed(url);

  return (
    <div className="vid-card">
      <div className="vid-frame">
        {embed && playing ? (
          embed.type === "iframe"
            ? <iframe src={embed.src + (embed.src.includes("?") ? "&" : "?") + "autoplay=1"} allow="autoplay; fullscreen; picture-in-picture" allowFullScreen title={name}></iframe>
            : <video src={embed.src} controls autoPlay playsInline></video>
        ) : (
          <>
            {embed && embed.thumb
              ? <img className="vid-thumb" src={embed.thumb} alt={name} onError={(e) => { e.target.style.display = "none"; }} />
              : <Ph label="VÍDEO VERTICAL 9:16" dark />}
            <button className="vid-play" onClick={() => embed && setPlaying(true)} style={{ position: "absolute" }} aria-label="Reproduzir">▶</button>
          </>
        )}
      </div>
      <div className="vid-meta">
        <div className="vid-stars">★★★★★</div>
        <p className="vid-quote">{quote}</p>
        <div className="vid-who"><span className="av"></span><b>{name}</b></div>
      </div>
    </div>
  );
}

// ═══════════════ TESTIMONIALS ═══════════════
function Testimonials() {
  const d = window.PROMO.testimonials;
  return (
    <section className="section tint">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
        </div>

        <div className="vid-grid reveal d1">
          {d.videos.map((v, i) => <VideoSlot key={i} url={v.url} quote={v.quote} name={v.name} />)}
        </div>

        <H as="h3" className="h3 reveal" html={d.moreTitleHtml} style={undefined} />
        <div className="prints">
          {d.prints.map((p, i) => (
            <div key={i} className={"print-card reveal d" + ((i % 4) + 1)}>
              <div className="print-head"><span className="pav"></span>{p.head}</div>
              <div className="print-body">
                {p.msgs.map((m, j) => (
                  <div key={j} className={"print-msg" + (p.them ? " them" : "")}>{m}</div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div style={{ textAlign: "center", marginTop: 40, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }} className="reveal d1">
          <a href={U().ajuda} className="btn btn-ghost">{d.more}</a>
          <a href={U().assinar} className="btn btn-go btn-lg">{d.cta} →</a>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ STORY ═══════════════
function Story() {
  const d = window.PROMO.story;
  return (
    <section className="section">
      <div className="container story-grid">
        <div className="reveal">
          <span className="kicker">{d.kicker}</span>
          <H as="h2" className="h2" html={d.titleHtml} />
          <div style={{ marginTop: 18 }}>
            {d.body.map((p, i) => <p key={i} className="lead" style={{ marginTop: 12 }}>{p}</p>)}
          </div>
          <H as="div" className="story-quote" html={d.quote} />
          <div className="story-stats">
            {d.stats.map((s, i) => (
              <div key={i} className="story-stat"><div className="n">{s.n}</div><div className="l">{s.l}</div></div>
            ))}
          </div>
        </div>
        <div className="story-media reveal d1"><img src="story-macbook.png" alt="FinanIA no MacBook" style={{ width: "100%", display: "block" }} /></div>
      </div>
    </section>
  );
}

// ═══════════════ BONUS ═══════════════
function Bonus() {
  const d = window.PROMO.bonus;
  return (
    <section className="section tint">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          {d.sub && <p className="lead reveal d1" style={{ maxWidth: 720, margin: "16px auto 0" }}>{d.sub}</p>}
        </div>
        {d.items.map((b, i) => (
          <div key={i} className={"bonus" + (b.flip ? " flip" : "")}>
            <div className="bonus-media reveal">{b.img ? <img src={b.img} alt={b.t} /> : <Ph label={b.ph} />}</div>
            <div className="reveal d1">
              <h4>{b.t}</h4>
              {b.sub && <p className="lead" style={{ margin: "0 0 16px" }}>{b.sub}</p>}
              <ul>{b.feats.map((f, j) => <li key={j}>{f}</li>)}</ul>
              <div className="bonus-price"><span className="old">De {b.old}</span> por <span className="new">R$ 0</span></div>
            </div>
          </div>
        ))}
        <div className="bonus-cards">
          {d.cards.map((c, i) => (
            <div key={i} className="bonus-card reveal d1">
              <div className="bonus-card-ic" aria-hidden="true">{c.icon}</div>
              <h5>{c.t}</h5>
              <p>{c.d}</p>
            </div>
          ))}
        </div>
        <div className="bonus-band reveal d1">
          <H as="p" html={d.bandHtml} />
          <a href={U().assinar} className="btn btn-primary">{d.bandCta}</a>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ OFFER (dark) — free + paid plans ═══════════════
function Offer() {
  const d = window.PROMO.offer;
  const u = U();
  const [annual, setAnnual] = React.useState(true);
  return (
    <section className="section dark" id="oferta">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2" style={{ margin: "16px auto 0" }}>{d.sub}</p>
        </div>

        {/* FREE highlight */}
        <div className="free-card reveal d1">
          <div className="free-left">
            <div className="free-badge">Plano {d.free.name}</div>
            <div className="free-price"><b>{d.free.price}</b> <span>{d.free.unit}</span></div>
            <p className="free-desc">{d.free.desc}</p>
            <a href={u.criarConta} className="btn btn-primary btn-lg">{d.free.cta} →</a>
          </div>
          <ul className="free-feats">
            {d.free.feats.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>

        {/* PAID plans */}
        <div className="plans-head reveal d1">
          <span className="plans-kicker">{d.plansKicker}</span>
          <div className="plan-toggle" role="group" aria-label="Periodicidade">
            <button aria-pressed={!annual} onClick={() => setAnnual(false)}>{d.monthlyLabel}</button>
            <button aria-pressed={annual} onClick={() => setAnnual(true)}>{d.annualLabel}</button>
          </div>
        </div>

        <div className="plan-grid">
          {d.plans.map((p, i) => (
            <div key={i} className={"plan-card reveal d" + ((i % 4) + 1) + (p.highlight ? " hl" : "")}>
              {p.tag && <div className="plan-card-tag">{p.tag}</div>}
              <div className="pc-name">{p.name}</div>
              <div className="pc-price">
                <span className="big">{annual ? p.annual : p.monthly}</span>
                <span className="per">{d.perMonth}</span>
              </div>
              <div className="pc-sub">{annual ? p.annualTotal : "cobrado mensalmente"}</div>
              <p className="pc-desc">{p.desc}</p>
              <ul className="pc-feats">{p.feats.map((f, j) => <li key={j}>{f}</li>)}</ul>
              <a href={u.assinar} className={"btn btn-block " + (p.highlight ? "btn-go" : "btn-ghost")} style={{ marginTop: "auto" }}>{d.cta}</a>
            </div>
          ))}
        </div>

        <p className="plan-guar reveal d1">🛡 {d.guaranteeNote}</p>

        {d.tableRows ? (
          <div className="cmp-full reveal d1">
            <h3 className="cmp-full-title">{d.tableTitle}</h3>
            <div className="cmp-full-scroll">
              <table className="cmp-full-table">
                <thead>
                  <tr>{d.tableHead.map((h, i) => <th key={i} className={i === 0 ? "l" : ""}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {d.tableRows.map((r, ri) => (
                    <tr key={ri}>
                      {r.map((c, ci) => (
                        <td key={ci} className={ci === 0 ? "l" : ""}>
                          {c === "y" ? <span className="t-yes">✓</span> : c === "n" ? <span className="t-no">×</span> : c}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="cmp-full-note">🔒 {d.mercadopago}</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

// ═══════════════ GUARANTEE (dark) ═══════════════
function Guarantee() {
  const d = window.PROMO.guarantee;
  return (
    <section className="dark" style={{ padding: "0 0 110px" }}>
      <div className="container guarantee">
        <div className="seal reveal">{d.seal}</div>
        <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
        <p className="lead reveal d2" style={{ marginTop: 16 }}>{d.body}</p>
      </div>
    </section>
  );
}

// ═══════════════ FAQ ═══════════════
function FaqItem({ q, a }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  return (
    <div className={"faq-item" + (open ? " open" : "")}>
      <button className="faq-q" onClick={() => setOpen(!open)}>
        <span>{q}</span>
        <svg className="chev" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg>
      </button>
      <div className="faq-a" style={{ maxHeight: open && ref.current ? ref.current.scrollHeight + "px" : "0px" }}>
        <div className="faq-a-inner" ref={ref}>{a}</div>
      </div>
    </div>
  );
}

function Faq() {
  const d = window.PROMO.faq;
  const half = Math.ceil(d.items.length / 2);
  const cols = [d.items.slice(0, half), d.items.slice(half)];
  return (
    <section className="section tint" id="faq">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <h2 className="h2 reveal d1">{d.title}</h2>
        </div>
        <div className="faq-grid">
          {cols.map((col, ci) => (
            <div key={ci} className="faq-col reveal d1">
              {col.map((it, i) => <FaqItem key={i} q={it.q} a={it.a} />)}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════ FINAL CTA ═══════════════
function FinalCta() {
  const d = window.PROMO.final;
  return (
    <section className="final">
      <div className="final-img"><img src="familia-praia.png" alt="Família feliz na praia" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} /></div>
      <div className="final-copy">
        <H as="h2" className="h2 reveal" html={d.titleHtml} />
        <p className="reveal d1">{d.body}</p>
        <p className="reveal d1">{d.body2}</p>
        <div className="price-line reveal d2">{d.price}</div>
        <a href={U().assinar} className="btn btn-go btn-lg reveal d2">{d.cta} →</a>
        <div className="final-guar reveal d3"><b>{d.guarStrong}</b>{d.guar}</div>
      </div>
    </section>
  );
}

// ═══════════════ FOOTER ═══════════════
function Footer() {
  const d = window.PROMO.footer;
  const u = U();
  const hrefFor = (l) => {
    const k = l.toLowerCase();
    if (k.includes("entrar")) return u.login;
    if (k.includes("ajuda")) return u.ajuda;
    if (k.includes("plano") || k.includes("faq") || k.includes("história")) return "#" + (k.includes("plano") ? "oferta" : "faq");
    return u.ajuda;
  };
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-top">
          <a className="footer-logo" href={u.ajuda}><img src="logo-finan.svg" alt="FiNan" /></a>
          <nav className="footer-links">
            {d.links.map((l, i) => <a key={i} href={hrefFor(l)}>{l}</a>)}
          </nav>
        </div>
        <div className="footer-bottom">
          <span>{d.copy} · {d.madein}</span>
          <span style={{ display: "flex", gap: 18 }}>
            {d.legal.map((l, i) => <a key={i} href={u[l.k] || u.ajuda} target="_blank" rel="noopener" style={{ color: "#8a8db3" }}>{l.t}</a>)}
          </span>
        </div>
      </div>
    </footer>
  );
}

Object.assign(window, { VideoSlot, Testimonials, Story, Bonus, Offer, Guarantee, Faq, FinalCta, Footer });
