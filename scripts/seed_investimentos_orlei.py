"""
Popula a base de Investimentos para o usuario 'orlei' com os dados
informados manualmente (carteiras de acoes, ETFs, RV/RF internacional,
renda fixa, fundos, cripto e previdencia).

Uso:
    docker exec -it finan_web python scripts/seed_investimentos_orlei.py
"""
from datetime import date

from app import create_app
from models import (
    db, User,
    InvestRendaFixa, InvestFundo, InvestCripto,
    InvestPrevidencia, InvestInternacional, InvestAtivo,
)

USERNAME = 'orlei'


def main():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=USERNAME).first()
        if not user:
            print(f"Usuario '{USERNAME}' nao encontrado.")
            return

        user_id = user.id
        print(f"Populando investimentos para user_id={user_id} ({user.username})")

        # ── Carteira de Acoes ──
        acoes = [
            ('ABEV3', 600, 15.69333333),
            ('ASAI3', 1800, 8.73333333),
            ('B3SA3', 600, 17.56066667),
            ('BBAS3', 1100, 22.70272727),
            ('BBDC4', 1400, 19.27071429),
            ('BBSE3', 300, 34.97333333),
            ('BRAP4', 300, 22.6125),
            ('CMIG4', 800, 12.14375),
            ('CPLE3', 500, 14.75),
            ('CSMG3', 200, 53.19),
            ('LREN3', 1000, 15.453),
            ('MRVE3', 500, 5.38),
            ('PETR4', 400, 41.8975),
            ('USIM5', 700, 7.35571429),
            ('WEGE3', 100, 47.35),
        ]
        for ticker, qtd, pm in acoes:
            db.session.add(InvestAtivo(
                user_id=user_id, ticker=ticker, type='ACAO',
                strategy='HOLDER', quantity=qtd, avg_price=round(pm, 4),
            ))

        # ── Carteira de ETFs ──
        etfs = [
            ('LFTB11', 40, 121.10),
            ('LFTS11', 40, 152.30),
        ]
        for ticker, qtd, pm in etfs:
            db.session.add(InvestAtivo(
                user_id=user_id, ticker=ticker, type='ETF',
                strategy='HOLDER', quantity=qtd, avg_price=pm,
            ))

        # ── Renda Fixa Internacional (RF) ──
        rf_intl = [
            ('SGOV', 9.96435748, 100.36, 100.51, 'INTER'),
            ('SHV', 3.178337109, 110.12, 110.19, 'INTER'),
            ('TFLO', 19.82191986, 50.45, 50.55, 'INTER'),
        ]
        for ticker, qtd, pm, cotacao, corretora in rf_intl:
            db.session.add(InvestInternacional(
                user_id=user_id, institution=corretora, name=ticker,
                quantity=qtd, avg_price=pm, quote=cotacao,
                category='RF', current_price=cotacao,
            ))

        # ── Renda Variavel Internacional (RV) ──
        rv_intl = [
            ('AMZN', 0.51903711, 229.89, 236.95, 'INTER'),
            ('ASML', 0.16982777, 1272.76, 1883.51, 'INTER'),
            ('BABA', 1.03141, 177.92, 111.67, 'Nomad'),
            ('BLK', 0.13332223532, 1088.30, 1037.89, 'INTER'),
            ('DAC', 1.0, 103.35, 131.45, 'NOMAD'),
            ('DIS', 0.88924818, 111.33, 100.06, 'INTER'),
            ('GOOG', 0.71714, 241.56, 362.38, 'AVENUE'),
            ('HRMY', 2.49196206, 36.92, 35.49, 'Inter'),
            ('JNJ', 0.6152, 187.71, 239.36, 'AVENUE'),
            ('JPM', 0.7496700000001, 309.02, 320.59, 'AVENUE'),
            ('LLY', 0.08493706, 1084.45, 1146.31, 'Inter'),
            ('META', 0.2396, 706.04, 570.22, 'AVENUE'),
            ('PRIM', 0.57049077, 127.96, 98.60, 'INTER'),
            ('TSLA', 0.34599, 426.14, 397.40, 'NOMAD'),
            ('TSM', 0.67001695, 322.38, 424.77, 'INTER'),
        ]
        for ticker, qtd, pm, cotacao, corretora in rv_intl:
            db.session.add(InvestInternacional(
                user_id=user_id, institution=corretora, name=ticker,
                quantity=qtd, avg_price=pm, quote=cotacao,
                category='RV', current_price=cotacao,
            ))

        # ── Renda Fixa Pos-Fixada ──
        rf_pos = [
            ('RDB', 'MERCADO PAGO', 'MP cofrinho', 10035.48, '120%', date(2025, 12, 27)),
            ('CDB', 'MERCADO PAGO', 'cdb ML 107', 21179.77, '110%', date(2026, 1, 15)),
            ('LCI', 'MERCADO PAGO', 'LCI MP Banco BRB', 5353.71, '100%', date(2026, 7, 1)),
            ('CDB', 'MERCADO PAGO', 'ML 107', 265.07, '107%', date(2026, 2, 1)),
            ('RDB', 'NUBANK', 'Caixinha', 10053.05, '120%', date(2025, 12, 27)),
            ('LCA', 'SANTANDER', 'LCA DI santander', 4083.18, '96%', date(2028, 7, 20)),
            ('LCA', 'BRADESCO', 'LCA DI', 1053.46, '100%', date(2029, 7, 20)),
            ('CRI', 'EQI', 'CRI MOURA DUBEUX', 5095.10, '100%', date(2030, 3, 15)),
            ('CDB', 'EQI', 'CDB BTG', 20831.83, '100%', date(2025, 12, 27)),
            ('CDB', 'EQI', 'BRB BANCO BRASILIA', 18738.65, '108%', date(2026, 4, 9)),
            ('LCA', 'EQI', 'LCA BANCO DES EXTREMO SUL', 7328.53, '100%', date(2027, 8, 30)),
            ('LCA', 'EQI', 'LCA BANCO DES EXTREMO SUL', 36688.87, '100%', date(2027, 8, 31)),
            ('LCA', 'NUBANK', 'LCA BANCO ORIGINAL', 3010.73, '92,5%', date(2027, 12, 20)),
            ('LCI', 'BRADESCO', 'LCI DI', 4557.22, '88%', date(2029, 11, 15)),
            ('CDB', 'BRADESCO', 'CAPITALO K10 MM', 3469.16, '100%', date(2026, 1, 29)),
            ('CDB', 'EQI', 'LIQQIDEZ DIARIA', 12494.31, '100%', date(2028, 2, 1)),
            ('CDB', 'BRADESCO', 'LIUIDEZ DIARIA', 100.00, '100%', date(2026, 2, 5)),
        ]
        for product_type, institution, name, value, rate, maturity in rf_pos:
            db.session.add(InvestRendaFixa(
                user_id=user_id, category='POS', product_type=product_type,
                institution=institution, name=name, value=value,
                rate=rate, maturity_date=maturity,
            ))

        # ── Renda Fixa Pre-Fixada ──
        rf_pre = [
            ('CDB', 'NUBANK', 'CDB banco C6', 4693.89, '11,70%', date(2026, 5, 11)),
            ('CDB', 'C6', 'C6 CDB 4 anos', 8854.90, '12,95%', date(2028, 5, 9)),
            ('CDB', 'C6', 'C6 CDB 4 anos', 1045.86, '12,20%', date(2028, 2, 15)),
            ('CDB', 'C6', 'C6 CDB 4 anos', 8533.73, '12,05%', date(2027, 12, 14)),
            ('CRA', 'EQI', 'EQI CRA MINERVA', 22410.11, '14,20%', date(2028, 9, 15)),
            ('CRA', 'EQI', 'EQI CRA FS FLORESTAL', 2168.91, '14,86%', date(2030, 3, 15)),
            ('CRA', 'EQI', 'EQI CRA MINERVA', 2220.60, '14,00%', date(2035, 4, 16)),
            ('LCA', 'EQI', 'LCA BTG', 1035.29, '12,72%', date(2026, 7, 2)),
            ('LCA', 'EQI', 'LCA BTG', 1029.18, '12,62%', date(2026, 9, 28)),
            ('LCA', 'EQI', 'LCA BTG', 5136.02, '12,60%', date(2026, 10, 2)),
            ('LCA', 'EQI', 'LCA ORIGINAL', 1011.79, '12,04%', date(2028, 11, 11)),
            ('LCI', 'BRADESCO', 'LCI Pre', 3500.00, '11,79%', date(2028, 2, 5)),
            ('CDB', 'EQI', 'BANCO ORIGINAL', 2000.00, '13,95%', date(2031, 2, 10)),
        ]
        for product_type, institution, name, value, rate, maturity in rf_pre:
            db.session.add(InvestRendaFixa(
                user_id=user_id, category='PRE', product_type=product_type,
                institution=institution, name=name, value=value,
                rate=rate, maturity_date=maturity,
            ))

        # ── Renda Fixa Inflacao (IPCA) ──
        rf_ipca = [
            ('Tesouro', 'SANTANDER', 'Tesouro IPCA 2060', 162.00, '7,06%', date(2060, 8, 15)),
            ('Tesouro', 'EQI', 'NTNB Juros semestrais 60', 5918.59, '7,12%', date(2060, 8, 16)),
            ('Tesouro', 'EQI', 'Aposentadoria Extra 65', 3768.99, '6,97%', date(2084, 12, 15)),
            ('CRI', 'EQI', 'ASSAI ATACADISTA', 2334.36, '8,12%', date(2028, 10, 16)),
            ('Tesouro', 'EQI', 'Tesouro IPCA 2050', 2400.03, '7,03%', date(2050, 8, 14)),
            ('CDB', 'EQI', 'BTG PACTUAL', 2505.36, '9,66%', date(2026, 12, 26)),
            ('CDB', 'EQI', 'RODOBENS SA', 4023.06, '8,46%', date(2027, 6, 23)),
            ('CDB', 'EQI', 'BANCO FIBRA', 5028.77, '8,45%', date(2027, 7, 15)),
            ('CDB', 'BRADESCO', 'BTG PACTUAL', 5007.43, '8,97%', date(2026, 12, 29)),
            ('CDB', 'BRADESCO', 'AGIBANK', 5004.83, '8,65%', date(2027, 12, 30)),
            ('CDB', 'BRADESCO', 'BANCO BMG SA', 4003.65, '7,91%', date(2028, 6, 30)),
            ('CDB', 'BRADESCO', 'BANCO BMG SA', 3002.56, '7,14%', date(2030, 12, 30)),
            ('CDB', 'BRADESCO', 'BANCO PINE', 5004.43, '8,5%', date(2029, 12, 31)),
            ('CDB', 'BRADESCO', 'BANCO RODOBENS SA', 4003.87, '8,66%', date(2027, 6, 30)),
            ('CDB', 'BRADESCO', 'BANCO AGIBANK SA', 5003.59, '8,3%', date(2029, 1, 2)),
            ('CDB', 'BRADESCO', 'BANCO PARANA', 4004.35, '7,33%', date(2030, 12, 30)),
            ('CDB', 'BRADESCO', 'BANCO PINE', 4003.55, '8,5%', date(2029, 12, 31)),
            ('CDB', 'C6', 'CDB C6', 10000.00, '9%', date(2027, 6, 30)),
            ('LCA', 'MERCADO PAGO', 'LCA BTG PACTUAL', 5012.13, '6,5%', date(2026, 12, 30)),
            ('CDB', 'EQI', 'BANCO PAN SA', 2000.00, 'IPCA+7,30', date(2031, 2, 5)),
            ('CDB', 'EQI', 'BANCO FIBRA SA', 2000.00, '7,8%', date(2030, 2, 15)),
            ('LCA', 'EQI', 'BTG PACTUAL', 2000.00, '5,38%', date(2030, 2, 15)),
            ('CDB', 'EQI', 'BANCO AGIBANK SA', 2000.00, '8%', date(2029, 2, 5)),
            ('CDB', 'EQI', 'BANCO FIBRA', 2000.00, '8,2%', date(2027, 8, 16)),
            ('CDB', 'EQI', 'BANCO ORIGINAL', 2000.00, '13,95%', date(2031, 2, 10)),
            ('CDB', 'EQI', 'BANCO BMG', 1000.00, '8,09%', date(2035, 2, 9)),
        ]
        for product_type, institution, name, value, rate, maturity in rf_ipca:
            db.session.add(InvestRendaFixa(
                user_id=user_id, category='IPCA', product_type=product_type,
                institution=institution, name=name, value=value,
                rate=rate, maturity_date=maturity,
            ))

        # ── Fundos de Investimento ──
        fundos = [
            ('EQI', 'LESTE RENDA BTS FUNDO', 32290.00, 'CDI', date(2032, 12, 27)),
            ('EQI', 'MANATI RENDA IMOBILIARIA', 10128.92, 'CDI', date(2026, 12, 27)),
        ]
        for institution, name, value, indexer, maturity in fundos:
            db.session.add(InvestFundo(
                user_id=user_id, institution=institution, name=name,
                value=value, indexer=indexer, maturity_date=maturity,
            ))

        # ── Criptoativos ──
        criptos = [
            ('EQI', 'BTC', 0.01236851, 532655.11, 6588.15, 323906.22),
            ('EQI', 'ETH', 0.0841984, 22513.59, 1893.84, 8478.83),
            ('MERCADO PAGO', 'BTC', 0.00084402, 389262.86, 328.55, 323906.22),
        ]
        for institution, name, quantity, avg_price, invested_value, quote in criptos:
            current_value = round(quantity * quote, 2)
            db.session.add(InvestCripto(
                user_id=user_id, institution=institution, name=name,
                quantity=quantity, avg_price=avg_price,
                invested_value=invested_value, current_value=current_value,
                quote=quote,
            ))

        # ── Previdencia ──
        previdencias = [
            ('EQI', 'BTG CRED CORP IIFIC CRPR', 10088.35, 'Renda Fixa'),
            ('EQI', 'BTG AUTIN BALANCEADO PREV FIM CRPR', 10106.41, 'Renda Fixa'),
            ('EQI', 'BTG CRED CORP IIFIC CRPR', 1820.16, 'Renda Fixa'),
            ('EQI', 'Angaprev Previdencia FIF RF', 2014.50, 'Renda Fixa'),
        ]
        for institution, name, value, tipo in previdencias:
            db.session.add(InvestPrevidencia(
                user_id=user_id, institution=institution, name=name,
                value=value, type=tipo,
            ))

        db.session.commit()
        print("Dados inseridos com sucesso!")


if __name__ == '__main__':
    main()
