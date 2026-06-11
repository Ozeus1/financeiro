import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Shield, AlertTriangle } from "lucide-react";
import { useState } from "react";

export default function Home() {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <header className="sticky top-0 z-50 text-white shadow-md" style={{ background: "linear-gradient(135deg,#1e3a8a 0%,#4361ee 55%,#7c3aed 100%)" }}>
        <div className="container py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-white" />
            <h1 className="text-2xl font-bold text-white">FinanIA</h1>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#compromisso" className="text-sm font-medium text-white/85 hover:text-white transition">
              Compromisso
            </a>
            <a href="#o-que-fazemos" className="text-sm font-medium text-white/85 hover:text-white transition">
              O que fazemos
            </a>
            <a href="#responsabilidade" className="text-sm font-medium text-white/85 hover:text-white transition">
              Responsabilidade
            </a>
            <Button variant="secondary" size="sm" asChild>
              <a href="/landing/">
                Voltar ao FinanIA
              </a>
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container py-16 md:py-24">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
            <Shield className="w-4 h-4" />
            Compliance e uso responsável
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 leading-tight" style={{ background: "linear-gradient(135deg,#1e3a8a 0%,#4361ee 55%,#7c3aed 100%)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>
            Transparência e responsabilidade no FinanIA
          </h2>
          <p className="text-lg text-slate-600 mb-8 leading-relaxed">
            O FinanIA foi criado para ajudar pessoas, famílias, autônomos e pequenos negócios a organizarem melhor suas informações financeiras. Nossa proposta é oferecer uma ferramenta de <strong>clareza, controle e prevenção</strong>.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <p className="text-blue-900 font-medium">
              <strong>O FinanIA é uma ferramenta de organização financeira.</strong> Ele não substitui advogado, contador, consultor financeiro, terapeuta, instituição financeira, órgão público ou entidade de defesa do consumidor.
            </p>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container py-12 md:py-16">
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {/* O que o FinanIA faz */}
          <Card id="o-que-fazemos" className="border-slate-200 shadow-sm hover:shadow-md transition">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                O que o FinanIA faz
              </CardTitle>
              <CardDescription>Funcionalidades e propósito da plataforma</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Classificação com IA</p>
                    <p className="text-sm text-slate-600">Categoriza despesas automaticamente para melhor organização</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Controle de faturas</p>
                    <p className="text-sm text-slate-600">Acompanha valores estimados e lançamentos de cartões</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Orçamento por categoria</p>
                    <p className="text-sm text-slate-600">Acompanha limites definidos pelo próprio usuário</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Relatórios e gráficos</p>
                    <p className="text-sm text-slate-600">Visualiza entradas, saídas, saldo e tendências</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* O que o FinanIA não promete */}
          <Card className="border-slate-200 shadow-sm hover:shadow-md transition">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                O que o FinanIA não promete
              </CardTitle>
              <CardDescription>Limitações e responsabilidades</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Não quita dívidas</p>
                    <p className="text-sm text-slate-600">Organiza informações, mas não elimina dívidas</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Não garante renegociação</p>
                    <p className="text-sm text-slate-600">Negociações dependem de credores e condições individuais</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Não trata compulsão</p>
                    <p className="text-sm text-slate-600">Não é serviço médico, psicológico ou terapêutico</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-600 mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-slate-900">Não substitui profissionais</p>
                    <p className="text-sm text-slate-600">Não oferece aconselhamento jurídico, contábil ou financeiro</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Seções expansíveis */}
        <div className="space-y-4">
          {/* Compromisso */}
          <Card id="compromisso" className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("compromisso")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Nosso compromisso</h3>
                <p className="text-sm text-slate-600 mt-1">Transparência e responsabilidade em cada funcionalidade</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "compromisso" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "compromisso" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4 text-slate-700">
                  <p>
                    O FinanIA não deve ser interpretado como promessa de eliminação de dívidas, enriquecimento, recuperação financeira garantida ou substituição de orientação profissional. O objetivo da plataforma é facilitar a organização dos dados financeiros para que o usuário tenha mais condições de compreender sua realidade e tomar decisões de forma consciente.
                  </p>
                  <p>
                    Adotamos uma comunicação responsável e não realizamos promessas incompatíveis com a natureza da ferramenta.
                  </p>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Superendividamento */}
          <Card className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("superendividamento")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Superendividamento e busca de orientação</h3>
                <p className="text-sm text-slate-600 mt-1">Quando procurar órgãos oficiais e profissionais</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "superendividamento" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "superendividamento" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4">
                  <p className="text-slate-700">
                    Pessoas em situação de endividamento grave, inadimplência persistente ou impossibilidade de pagar dívidas sem comprometer despesas essenciais devem buscar orientação adequada.
                  </p>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-900 font-medium mb-2">Recomendamos procurar:</p>
                    <ul className="text-red-800 text-sm space-y-1">
                      <li>• <strong>Procon</strong> — Órgão de defesa do consumidor</li>
                      <li>• <strong>Defensoria Pública</strong> — Assistência jurídica gratuita</li>
                      <li>• <strong>Centros judiciários de solução de conflitos</strong> — Mediação de dívidas</li>
                      <li>• <strong>Advogados especializados</strong> — Orientação jurídica</li>
                      <li>• <strong>Contadores qualificados</strong> — Orientação contábil</li>
                    </ul>
                  </div>
                  <p className="text-slate-700">
                    O FinanIA pode ajudar o usuário a organizar informações importantes para essa etapa, como lista de dívidas, despesas mensais, receitas e histórico financeiro. No entanto, a plataforma não decide estratégias jurídicas, não negocia automaticamente com credores e não garante aceitação de propostas de pagamento.
                  </p>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Apostas e compulsão */}
          <Card className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("apostas")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Apostas, compulsão e saúde mental</h3>
                <p className="text-sm text-slate-600 mt-1">Quando procurar apoio profissional</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "apostas" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "apostas" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4">
                  <p className="text-slate-700">
                    O FinanIA pode ajudar o usuário a identificar gastos recorrentes, inclusive despesas relacionadas a apostas, jogos, compras por impulso ou outras categorias de consumo. Essa visualização pode ser útil para reconhecer padrões financeiros, mas não constitui diagnóstico, tratamento ou cura de vício, compulsão, transtorno mental ou sofrimento emocional.
                  </p>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <p className="text-purple-900 font-medium mb-2">Se você perceber:</p>
                    <ul className="text-purple-800 text-sm space-y-1">
                      <li>• Perda de controle sobre gastos</li>
                      <li>• Sofrimento emocional relacionado a dinheiro</li>
                      <li>• Endividamento recorrente</li>
                      <li>• Prejuízo familiar ou profissional</li>
                      <li>• Dificuldade de interromper determinado comportamento</li>
                    </ul>
                  </div>
                  <p className="text-slate-700">
                    Recomendamos buscar apoio profissional de saúde, serviços públicos competentes, grupos de apoio ou atendimento especializado.
                  </p>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Inteligência Artificial */}
          <Card className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("ia")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Inteligência artificial e limitações</h3>
                <p className="text-sm text-slate-600 mt-1">Como a IA funciona e suas limitações</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "ia" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "ia" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4 text-slate-700">
                  <p>
                    O FinanIA utiliza recursos de inteligência artificial para apoiar tarefas como categorização, leitura, organização, resposta a perguntas e geração de relatórios. Embora esses recursos possam facilitar o controle financeiro, eles podem apresentar erros, incompletudes, classificações imprecisas ou interpretações inadequadas quando os dados forem insuficientes, ambíguos ou importados com inconsistências.
                  </p>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-900 font-medium">Importante:</p>
                    <p className="text-yellow-800 text-sm mt-2">
                      O usuário deve revisar informações importantes antes de tomar decisões financeiras relevantes. A responsabilidade por conferir lançamentos, confirmar categorias, validar saldos, revisar relatórios e decidir como agir permanece com o usuário.
                    </p>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Responsabilidade do usuário */}
          <Card id="responsabilidade" className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("usuario")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Responsabilidade do usuário</h3>
                <p className="text-sm text-slate-600 mt-1">Seu papel na utilização responsável</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "usuario" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "usuario" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4">
                  <p className="text-slate-700">
                    O usuário é responsável por fornecer dados corretos, revisar informações importadas, confirmar lançamentos, proteger seus acessos e utilizar a plataforma de forma compatível com a legislação aplicável.
                  </p>
                  <div className="space-y-3">
                    <div className="flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-slate-900">Forneça dados corretos</p>
                        <p className="text-sm text-slate-600">Informações precisas garantem relatórios confiáveis</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-slate-900">Revise informações importantes</p>
                        <p className="text-sm text-slate-600">Antes de tomar decisões financeiras relevantes</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-slate-900">Proteja seus acessos</p>
                        <p className="text-sm text-slate-600">Mantenha senhas protegidas e evite compartilhamento</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-slate-900">Busque orientação profissional</p>
                        <p className="text-sm text-slate-600">Quando necessário, para decisões de impacto patrimonial</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Privacidade */}
          <Card id="privacidade" className="border-slate-200 shadow-sm">
            <button
              onClick={() => toggleSection("privacidade")}
              className="w-full text-left p-6 hover:bg-slate-50 transition flex items-center justify-between"
            >
              <div>
                <h3 className="text-lg font-bold text-slate-900">Privacidade e segurança</h3>
                <p className="text-sm text-slate-600 mt-1">Como protegemos seus dados</p>
              </div>
              <div className={`text-slate-400 transition-transform ${expandedSection === "privacidade" ? "rotate-180" : ""}`}>
                ▼
              </div>
            </button>
            {expandedSection === "privacidade" && (
              <CardContent className="border-t border-slate-200 pt-6 pb-6">
                <div className="space-y-4 text-slate-700">
                  <p>
                    O FinanIA deve ser utilizado de acordo com sua Política de Privacidade, Termos de Uso e demais documentos legais aplicáveis. A plataforma adota medidas de segurança para proteção dos dados, mas o usuário também deve contribuir para a segurança de sua conta.
                  </p>
                  <p>
                    Sempre que houver tratamento de dados pessoais, a utilização da plataforma deve observar a legislação aplicável, incluindo a Lei Geral de Proteção de Dados Pessoais (LGPD), quando pertinente.
                  </p>
                </div>
              </CardContent>
            )}
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container py-16 md:py-20">
        <div className="rounded-2xl p-8 md:p-12 text-white text-center" style={{ background: "linear-gradient(135deg,#1e3a8a 0%,#4361ee 55%,#7c3aed 100%)" }}>
          <h3 className="text-3xl md:text-4xl font-bold mb-4">Pronto para começar?</h3>
          <p className="text-blue-100 mb-8 max-w-2xl mx-auto text-lg">
            Organize suas finanças com clareza, controle e prevenção. Comece grátis, sem cartão de crédito.
          </p>
          <Button size="lg" variant="secondary" className="text-blue-600 hover:text-blue-700" asChild>
            <a href="/landing/">
              Ir para FinanIA
            </a>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50 py-12">
        <div className="container">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="font-bold text-slate-900 mb-4">FinanIA</h4>
              <p className="text-sm text-slate-600">Organização financeira com inteligência artificial.</p>
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-4">Links</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="/landing/" className="text-slate-600 hover:text-blue-600 transition">
                    Site principal
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="#privacidade" className="text-slate-600 hover:text-blue-600 transition">
                    Privacidade e segurança
                  </a>
                </li>
                <li>
                  <a href="#compromisso" className="text-slate-600 hover:text-blue-600 transition">
                    Nosso compromisso
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-4">Contato</h4>
              <p className="text-sm text-slate-600">
                <a href="mailto:contato@finania.pro" className="hover:text-blue-600 transition">
                  contato@finania.pro
                </a>
              </p>
            </div>
          </div>
          <div className="border-t border-slate-200 pt-8 flex flex-col md:flex-row items-center justify-between">
            <p className="text-sm text-slate-600">© 2026 FinanIA. Todos os direitos reservados.</p>
            <p className="text-sm text-slate-600 mt-4 md:mt-0">
              Última atualização: junho de 2026
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
