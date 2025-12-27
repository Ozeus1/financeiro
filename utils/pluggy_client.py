import requests
import json
from datetime import datetime, timedelta

class PluggyClient:
    """Cliente para interação com a API da Pluggy (Open Finance)"""
    
    BASE_URL = "https://api.pluggy.ai"
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = None
        
    def authenticate(self):
        """Autentica na API e obtém o API Key"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Credenciais da Pluggy (Client ID e Secret) não configuradas.")
            
        url = f"{self.BASE_URL}/auth"
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.api_key = data.get("apiKey")
            return self.api_key
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro na autenticação Pluggy: {str(e)}"
            if response and response.text:
                error_msg += f" - Detalhes: {response.text}"
            raise Exception(error_msg)

    def _get_headers(self):
        """Retorna headers padrão para requisições"""
        if not self.api_key:
            self.authenticate()
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-KEY": self.api_key
        }

    def get_accounts(self, item_id):
        """Obtém contas vinculadas a um item"""
        url = f"{self.BASE_URL}/accounts?itemId={item_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao buscar contas: {str(e)}")

    def get_transactions(self, account_id, from_date=None, to_date=None):
        """
        Obtém transações de uma conta
        Data formato: YYYY-MM-DD
        """
        if not from_date:
            # Padrão: últimos 30 dias
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        url = f"{self.BASE_URL}/transactions?accountId={account_id}&from={from_date}"
        if to_date:
            url += f"&to={to_date}"
            
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao buscar transações: {str(e)}")
            
    def get_item(self, item_id):
        """Obtém detalhes de uma conexão (item)"""
        url = f"{self.BASE_URL}/items/{item_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao buscar item: {str(e)}")
            
    def create_connect_token(self):
        """Cria um token para o widget de conexão"""
        url = f"{self.BASE_URL}/connect_token"
        
        try:
            response = requests.post(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("accessToken")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao criar connect token: {str(e)}")
