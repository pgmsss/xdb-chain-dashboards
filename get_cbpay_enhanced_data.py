#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Este script coleta dados dos detentores do token CBPAY da XDB Chain
# e informações adicionais do token (preço, volume, market cap) do CoinGecko
# e os salva em arquivos JSON para uso em páginas web estáticas.

import requests
import json
import os
from datetime import datetime

# XDB Chain API Configuration
HORIZON_URL = "https://horizon.livenet.xdbchain.com/accounts"
ASSET_CODE = "CBPAY"
ASSET_ISSUER = "GD7PT6VAXH227WBYR5KN3OYKGSNXVETMYZUP3R62DFX3BBC7GGOBDFJ2"

# CoinGecko API Configuration
COINGECKO_API_KEY = "CG-8CoKVLYmm4crygn9DeHvFUAk"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

def get_all_cbpay_holders():
    """Coleta todos os detentores do token CBPAY da XDB Chain"""
    all_holders = []
    params = {
        "asset": f"{ASSET_CODE}:{ASSET_ISSUER}",
        "limit": 200,
        "order": "asc",
        "cursor": None
    }

    while True:
        print(f"Buscando página com cursor: {params['cursor']}")
        response = requests.get(HORIZON_URL, params=params)
        response.raise_for_status()
        data = response.json()
        records = data["_embedded"]["records"]

        if not records:
            break

        for record in records:
            for balance_info in record["balances"]:
                if balance_info["asset_type"] != "native" and \
                   balance_info["asset_code"] == ASSET_CODE and \
                   balance_info["asset_issuer"] == ASSET_ISSUER:
                    all_holders.append({
                        "address": record["id"],
                        "balance": float(balance_info["balance"])
                    })
                    break

        # Get the next page of results
        if "next" in data["_links"] and "href" in data["_links"]["next"]:
            next_page_url = data["_links"]["next"]["href"]
            if 'cursor=' in next_page_url:
                params["cursor"] = next_page_url.split('cursor=')[-1].split('&')[0]
            else:
                break
        else:
            break

    return all_holders

def get_cbpay_market_data():
    """Obtém dados de mercado do CBPAY do CoinGecko"""
    try:
        # Primeiro, vamos tentar encontrar o ID do CBPAY no CoinGecko
        search_url = f"{COINGECKO_BASE_URL}/search"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        
        search_params = {"query": "coinbarpay"}
        search_response = requests.get(search_url, headers=headers, params=search_params)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"Resultados da pesquisa CoinGecko: {search_data}")
            
            # Procurar por CBPAY nos resultados
            cbpay_coin = None
            if "coins" in search_data:
                for coin in search_data["coins"]:
                    if coin.get("symbol", "").upper() == "CBPAY" or "coinbar" in coin.get("name", "").lower():
                        cbpay_coin = coin
                        break
            
            if cbpay_coin:
                coin_id = cbpay_coin["id"]
                print(f"Encontrado CBPAY no CoinGecko com ID: {coin_id}")
                
                # Obter dados de preço
                price_url = f"{COINGECKO_BASE_URL}/simple/price"
                price_params = {
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true"
                }
                
                price_response = requests.get(price_url, headers=headers, params=price_params)
                
                if price_response.status_code == 200:
                    price_data = price_response.json()
                    if coin_id in price_data:
                        return {
                            "price_usd": price_data[coin_id].get("usd", 0),
                            "market_cap_usd": price_data[coin_id].get("usd_market_cap", 0),
                            "volume_24h_usd": price_data[coin_id].get("usd_24h_vol", 0),
                            "price_change_24h": price_data[coin_id].get("usd_24h_change", 0),
                            "last_updated": datetime.now().isoformat(),
                            "source": "CoinGecko"
                        }
        
        # Se não encontrou no CoinGecko, retorna dados padrão
        print("CBPAY não encontrado no CoinGecko, usando dados padrão")
        return {
            "price_usd": 0,
            "market_cap_usd": 0,
            "volume_24h_usd": 0,
            "price_change_24h": 0,
            "last_updated": datetime.now().isoformat(),
            "source": "Not Available",
            "note": "CBPAY data not available on CoinGecko"
        }
        
    except Exception as e:
        print(f"Erro ao obter dados do CoinGecko: {e}")
        return {
            "price_usd": 0,
            "market_cap_usd": 0,
            "volume_24h_usd": 0,
            "price_change_24h": 0,
            "last_updated": datetime.now().isoformat(),
            "source": "Error",
            "error": str(e)
        }

def get_recent_large_transactions():
    """Obtém as transações mais recentes e identifica as maiores"""
    try:
        payments_url = "https://horizon.livenet.xdbchain.com/payments"
        params = {
            "asset_code": ASSET_CODE,
            "asset_issuer": ASSET_ISSUER,
            "limit": 200,
            "order": "desc"  # Mais recentes primeiro
        }
        
        response = requests.get(payments_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        large_transactions = []
        if "_embedded" in data and "records" in data["_embedded"]:
            for record in data["_embedded"]["records"]:
                if record.get("asset_code") == ASSET_CODE and record.get("asset_issuer") == ASSET_ISSUER:
                    amount = float(record.get("amount", 0))
                    if amount >= 100000:  # Considerar transações >= 100k CBPAY como "grandes"
                        large_transactions.append({
                            "amount": amount,
                            "from": record.get("from"),
                            "to": record.get("to"),
                            "date": record.get("created_at"),
                            "transaction_hash": record.get("transaction_hash")
                        })
        
        # Ordenar por valor (maior primeiro) e pegar as top 10
        large_transactions.sort(key=lambda x: x["amount"], reverse=True)
        return large_transactions[:10]
        
    except Exception as e:
        print(f"Erro ao obter transações grandes: {e}")
        return []

if __name__ == "__main__":
    print("Iniciando a coleta de dados aprimorados do token CBPAY...")
    
    # Coletar dados dos detentores
    print("1. Coletando dados dos detentores...")
    holders_data = get_all_cbpay_holders()
    holders_data.sort(key=lambda x: x["balance"], reverse=True)
    print(f"Total de detentores encontrados: {len(holders_data)}")
    
    # Coletar dados de mercado
    print("2. Coletando dados de mercado do CoinGecko...")
    market_data = get_cbpay_market_data()
    
    # Coletar grandes transações
    print("3. Coletando grandes transações...")
    large_transactions = get_recent_large_transactions()
    print(f"Grandes transações encontradas: {len(large_transactions)}")
    
    # Salvar dados dos detentores
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    holders_file = os.path.join(output_dir, "cbpay_holders.json")
    with open(holders_file, "w") as f:
        json.dump(holders_data, f, indent=4)
    print(f"Dados dos detentores salvos em {holders_file}")
    
    # Salvar dados de mercado
    market_file = os.path.join(output_dir, "cbpay_market_data.json")
    with open(market_file, "w") as f:
        json.dump(market_data, f, indent=4)
    print(f"Dados de mercado salvos em {market_file}")
    
    # Salvar grandes transações
    transactions_file = os.path.join(output_dir, "cbpay_large_transactions.json")
    with open(transactions_file, "w") as f:
        json.dump(large_transactions, f, indent=4)
    print(f"Grandes transações salvas em {transactions_file}")
    
    # Mostrar resumo
    print("\n=== RESUMO ===")
    print(f"Total de detentores: {len(holders_data)}")
    if market_data['source'] != "Error":
        print(f"Preço atual: ${market_data['price_usd']:.8f} USD")
        print(f"Market Cap: ${market_data['market_cap_usd']:,.2f} USD")
        print(f"Volume 24h: ${market_data['volume_24h_usd']:,.2f} USD")
        print(f"Mudança 24h: {market_data['price_change_24h']:.2f}%")
    print(f"Grandes transações recentes: {len(large_transactions)}")
    
    if holders_data:
        print("\nTop 5 Maiores Detentores:")
        for i, holder in enumerate(holders_data[:5]):
            print(f"  {i+1}. {holder['address']}: {holder['balance']:,.2f} CBPAY")

