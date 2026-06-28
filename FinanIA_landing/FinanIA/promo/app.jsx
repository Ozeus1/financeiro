// FinanIA Promo — app assembly.
function PromoApp() {
  useReveal();
  return (
    <React.Fragment>
      <Urgency />
      <Nav />
      <Hero />
      <Stats />
      <Situations />
      <Comparison />
      <Cycle />
      <Devices />
      <Platform />
      <Features />
      <Showcases />
      <WhatsApp />
      <Testimonials />
      <Story />
      <Bonus />
      <Offer />
      <Guarantee />
      <Faq />
      <FinalCta />
      <Footer />
    </React.Fragment>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<PromoApp />);
