
from datetime import datetime

# Mock classes
class MockUser:
    id = 1

current_user = MockUser()

class MockModel:
    def query(self): return self
    def filter_by(self, **kwargs): return self
    def first(self): return None
    def order_by(self, *args): return self
    def all(self): return []

Despesa = MockModel()
Receita = MockModel()
CategoriaDespesa = MockModel()
CategoriaReceita = MockModel()

# Mock data
accounts = [
    {'id': 'acc_credit', 'type': 'CREDIT'},
    {'id': 'acc_bank', 'type': 'BANK'}
]

transactions_mock = {
    'acc_credit': [
        {'id': 1, 'amount': -100.0, 'description': 'Compra Supermercado', 'date': '2023-10-01T10:00:00Z'},
        {'id': 2, 'amount': 20.0, 'description': 'Estorno Taxa', 'date': '2023-10-02T10:00:00Z'},
        {'id': 3, 'amount': 1000.0, 'description': 'Pagamento Fatura', 'date': '2023-10-03T10:00:00Z'}, # Should become Expense (-1000)
    ],
    'acc_bank': [
        {'id': 4, 'amount': -50.0, 'description': 'Tarifa', 'date': '2023-10-01T10:00:00Z'},
        {'id': 5, 'amount': 2000.0, 'description': 'Salário', 'date': '2023-10-05T10:00:00Z'},
    ]
}

def simulate_import():
    transactions_display = []
    
    # Mock category setup
    cat_outros_despesa = type('obj', (object,), {'id': 99, 'nome': 'Outros'})
    cat_outros_receita = type('obj', (object,), {'id': 100, 'nome': 'Outros'})
    cats_despesa = [cat_outros_despesa]
    cats_receita = [cat_outros_receita]

    print("--- Simulating Import ---")

    for account in accounts:
        acc_type = account.get('type')
        print(f"\nProcessing Account: {acc_type}")
        
        transactions = transactions_mock[account['id']]
        
        for tr in transactions:
            amount = tr.get('amount')
            description = tr.get('description')
            date_str = tr.get('date').split('T')[0]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            exists = False
            suggested_cat_id = None
            
            # --- LOGIC START ---
            if acc_type == 'CREDIT':
                if amount > 0:
                    if 'estorno' not in description.lower():
                        amount = -abs(amount)
            # --- LOGIC END ---

            if amount < 0:
                type_str = "DESPESA"
            else:
                type_str = "RECEITA"
            
            print(f"  Tx: {description:<20} | Orig Amount: {tr.get('amount'):>8} | New Amount: {amount:>8} | Classified as: {type_str}", flush=True)

simulate_import()
