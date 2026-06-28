// FinanIA Promo — sections 2 (devices, platform 3-up, feature showcases, whatsapp).

// ═══════════════ DEVICES (dark) ═══════════════
function Devices() {
  const d = window.PROMO.devices;
  const DM = window.DeviceMock;
  return (
    <section className="section dark">
      <div className="container devices">
        <span className="kicker reveal">{d.kicker}</span>
        <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
        <p className="lead reveal d2" style={{ maxWidth: 620, margin: "16px auto 0" }}>{d.sub}</p>
        <div className="devices-shot reveal d2">
          <div className="devices-duo">
            <img className="dev-desk" src="sec-devices.png" alt="FinanIA no desktop" />
            <img className="dev-phone" src="sec-devices-phone.png" alt="Assistente FinanIA no WhatsApp" />
          </div>
        </div>
        <div className="dev-features">
          {d.features.map((f, i) => (
            <div key={i} className={"dev-feat reveal d" + (i + 1)}>
              <div className="di"><Icon n={f.i} /></div>
              <div><h4>{f.t}</h4><p>{f.d}</p></div>
            </div>
          ))}
        </div>
        <div className="reveal d3" style={{ marginTop: 44 }}>
          <a href={U().assinar} className="btn btn-primary btn-lg">{d.cta} →</a>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ PLATFORM 3-up (tint) ═══════════════
function Platform() {
  const d = window.PROMO.platform;
  return (
    <section className="section tint">
      <div className="container">
        <div className="section-head">
          <span className="plat-toggle reveal">☀ {d.badge}</span>
          <div style={{ height: 18 }} />
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2">{d.sub}</p>
        </div>
        <div className="plat-3">
          {d.items.map((it, i) => (
            <div key={i} className={"plat-item reveal d" + (i + 1)}>
              <div className="pi"><Icon n={it.i} /></div>
              <h4>{it.t}</h4>
              <p>{it.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════ FEATURE SHOWCASES ═══════════════
function Showcases() {
  const list = window.PROMO.showcases;
  return (
    <section className="section">
      <div className="container">
        {list.map((s, i) => (
          <div key={i} className={"showcase" + (s.flip ? " flip" : "")}>
            <div className="sc-media reveal">
              <img src={s.img} alt={s.kicker} />
            </div>
            <div className="reveal d1">
              <span className="sc-kicker">{s.kicker}</span>
              <H as="h3" className="h3" html={s.titleHtml} />
              <p className="lead">{s.body}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ═══════════════ WHATSAPP (dark) ═══════════════
function WhatsApp() {
  const d = window.PROMO.whatsapp;
  return (
    <section className="section dark">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2" style={{ margin: "16px auto 0" }}>{d.sub}</p>
        </div>
        <div className="wa-icons reveal d1">
          <div className="wi ai"><Icon n="ai" /></div>
          <span className="plus">+</span>
          <div className="wi wpp">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15l-1.4 5 5.1-1.3A10 10 0 1 0 12 2zm0 18a8 8 0 0 1-4-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1 1 12 20zm4.4-6c-.2-.1-1.4-.7-1.6-.8s-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.6 6.6 0 0 1-3.2-2.8c-.2-.4.2-.4.6-1.2.1-.2 0-.3 0-.5l-.7-1.7c-.2-.5-.4-.4-.5-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-1 2.3 5.3 5.3 0 0 0 1.1 2.8 12 12 0 0 0 4.6 4c2 .8 2 .6 2.4.5a2.6 2.6 0 0 0 1.7-1.2 2.1 2.1 0 0 0 .1-1.2c0-.1-.2-.2-.4-.3z"/></svg>
          </div>
        </div>
        <H as="div" className="wa-callout reveal d2" html={d.callout} />

        <div className="wa-cap">
          {d.caps.map((c, i) => (
            <div key={i} className={"wa-caprow reveal d" + ((i % 3) + 1)}>
              <div className="wci"><Icon n={c.i} /></div>
              <div><h4>{c.t}</h4><p>{c.d}</p></div>
            </div>
          ))}
        </div>

        <div className="wa-photo reveal d2">
          <img src="wa-phone.png" alt="Assistente FinanIA respondendo no WhatsApp" />
        </div>

        <div className="wa-band reveal d1">
          <H as="h3" className="h3" html={d.bandTitle} />
          <p>{d.bandText}</p>
        </div>

        <div style={{ textAlign: "center", marginTop: 44 }} className="reveal d1">
          <a href={U().assinar} className="btn btn-go btn-lg">{d.cta} →</a>
          <p style={{ color: "#9a9cc4", fontSize: 13.5, marginTop: 14 }}>{d.guar}</p>
        </div>
      </div>
    </section>
  );
}

// ═══════════════ FEATURES (Recursos grid) ═══════════════
function Features() {
  const d = window.PROMO.features;
  return (
    <section className="section tint" id="recursos">
      <div className="container">
        <div className="section-head">
          <span className="kicker reveal">{d.kicker}</span>
          <H as="h2" className="h2 reveal d1" html={d.titleHtml} />
          <p className="lead reveal d2">{d.sub}</p>
        </div>
        <div className="feat-grid">
          {d.items.map((f, i) => (
            <div key={i} className={"feat-card reveal d" + ((i % 4) + 1)}>
              <div className="feat-ic"><Icon n={f.i} /></div>
              <div className="feat-tag">{f.tag}</div>
              <h4>{f.t}</h4>
              <p>{f.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { Devices, Platform, Features, Showcases, WhatsApp });
