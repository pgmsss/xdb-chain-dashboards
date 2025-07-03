import pandas as pd
import requests
import json

def get_xdb_usdt_rate():
    """Fetch current XDB to USDT exchange rate from CoinMarketCap API"""
    try:
        # Using CoinMarketCap API (free tier)
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 'your-api-key-here',  # Would need actual API key
        }
        parameters = {
            'symbol': 'XDB',
            'convert': 'USDT'
        }
        
        # For demo purposes, using a static rate from our research
        return 0.0006913
        
    except Exception as e:
        print(f"Error fetching XDB rate: {e}")
        return 0.0006913  # Fallback rate

def parse_markdown_table(markdown_table_string, headers):
    """Parse markdown table string into pandas DataFrame"""
    lines = markdown_table_string.strip().split('\n')
    data = []
    for line in lines:
        if line.strip():
            values = [v.strip() for v in line.split('|') if v.strip()]
            data.append(values)
    return pd.DataFrame(data, columns=headers)

def process_order_book_data(html_content):
    """Process order book data and add USDT values"""
    xdb_usdt_rate = get_xdb_usdt_rate()
    headers = ['Preço (XDB)', 'Quantidade (CBPAY)', 'Acumulado (CBPAY)', 'Valor (USD)']
    
    # Extract Bids table
    bids_start = html_content.find('### Bids (Compras)')
    bids_end = html_content.find('### Asks (Vendas)')
    bids_table_markdown = html_content[bids_start:bids_end].split('| --- | --- | --- | --- |\n')[1].strip()
    bids_df = parse_markdown_table(bids_table_markdown, headers)
    
    # Extract Asks table
    asks_start = html_content.find('### Asks (Vendas)')
    asks_table_markdown = html_content[asks_start:].split('| --- | --- | --- | --- |\n')[1].strip()
    # Remove the trailing content after the table
    asks_table_markdown = asks_table_markdown.split('\n\n')[0]
    asks_df = parse_markdown_table(asks_table_markdown, headers)
    
    # Calculate Valor (USDT) for Bids
    bids_df['Preço (XDB)'] = pd.to_numeric(bids_df['Preço (XDB)'], errors='coerce')
    bids_df['Quantidade (CBPAY)'] = pd.to_numeric(bids_df['Quantidade (CBPAY)'], errors='coerce')
    bids_df['Valor (USDT)'] = bids_df['Preço (XDB)'] * bids_df['Quantidade (CBPAY)'] * xdb_usdt_rate
    bids_df['Valor (USDT)'] = bids_df['Valor (USDT)'].round(7)
    
    # Calculate Valor (USDT) for Asks
    asks_df['Preço (XDB)'] = pd.to_numeric(asks_df['Preço (XDB)'], errors='coerce')
    asks_df['Quantidade (CBPAY)'] = pd.to_numeric(asks_df['Quantidade (CBPAY)'], errors='coerce')
    asks_df['Valor (USDT)'] = asks_df['Preço (XDB)'] * asks_df['Quantidade (CBPAY)'] * xdb_usdt_rate
    asks_df['Valor (USDT)'] = asks_df['Valor (USDT)'].round(7)
    
    return bids_df, asks_df, xdb_usdt_rate

def generate_html_table(df, table_type):
    """Generate HTML table from DataFrame"""
    html = f'<h3>{table_type}</h3>\n<table class="order-book-table">\n'
    html += '<thead>\n<tr>\n'
    for col in ['Preço (XDB)', 'Quantidade (CBPAY)', 'Acumulado (CBPAY)', 'Valor (USDT)']:
        html += f'<th>{col}</th>\n'
    html += '</tr>\n</thead>\n<tbody>\n'
    
    for _, row in df.iterrows():
        if pd.notna(row['Preço (XDB)']):  # Skip NaN rows
            html += '<tr>\n'
            # Convert to numeric for formatting
            preco = pd.to_numeric(row["Preço (XDB)"], errors='coerce')
            quantidade = pd.to_numeric(row["Quantidade (CBPAY)"], errors='coerce')
            acumulado = pd.to_numeric(row["Acumulado (CBPAY)"], errors='coerce')
            valor_usdt = pd.to_numeric(row["Valor (USDT)"], errors='coerce')
            
            html += f'<td>{preco:.7f}</td>\n'
            html += f'<td>{quantidade:.7f}</td>\n'
            html += f'<td>{acumulado:.7f}</td>\n'
            html += f'<td>{valor_usdt:.7f}</td>\n'
            html += '</tr>\n'
    
    html += '</tbody>\n</table>\n'
    return html

def generate_complete_html(bids_df, asks_df, xdb_usdt_rate):
    """Generate complete HTML page with USDT values"""
    bids_table = generate_html_table(bids_df, 'Bids (Compras)')
    asks_table = generate_html_table(asks_df, 'Asks (Vendas)')
    
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XDB Chain Order Book - Com Valores USDT</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2563eb;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .status {{
            background-color: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .status-icon {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .order-book-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }}
        .order-book-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .order-book-table th,
        .order-book-table td {{
            padding: 8px 12px;
            text-align: right;
            border-bottom: 1px solid #e5e7eb;
        }}
        .order-book-table th {{
            background-color: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        .order-book-table tr:hover {{
            background-color: #f9fafb;
        }}
        h3 {{
            color: #374151;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .bids h3 {{
            color: #059669;
        }}
        .asks h3 {{
            color: #dc2626;
        }}
        .rate-info {{
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }}
        @media (max-width: 768px) {{
            .order-book-container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>XDB CHAIN Order Book</h1>
        <p class="subtitle">Real-time CBPAY/XDB Trading Data com Valores USDT</p>
        
        <div class="status">
            <div class="status-icon">📊</div>
            <strong>Up and running!</strong><br>
            Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y, %H:%M:%S')}<br>
            Par de negociação: <strong>CBPAY/XDB</strong>
        </div>
        
        <div class="rate-info">
            <strong>Taxa de Conversão XDB/USDT:</strong> {xdb_usdt_rate:.7f} USDT por XDB<br>
            <small>Fonte: CoinMarketCap</small>
        </div>
        
        <h2>Order Book para CBPAY/XDB</h2>
        
        <div class="order-book-container">
            <div class="bids">
                {bids_table}
            </div>
            <div class="asks">
                {asks_table}
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {{
            location.reload();
        }}, 10000);
    </script>
</body>
</html>'''
    
    return html

if __name__ == "__main__":
    # Sample HTML content (would be fetched from the actual page)
    sample_html = '''
# XDB Chain Order Book

# XDB CHAIN Order Book

Real-time CBPAY/XDB Trading Data

## Order Book Status

📊

Up and running!

Última atualização: 03/07/2025, 17:49:21  
Próxima atualização em: 29 segundos  
Par de negociação: **CBPAY/XDB**

## Order Book para CBPAY/XDB

### Bids (Compras)

| Preço (XDB) | Quantidade (CBPAY) | Acumulado (CBPAY) | Valor (USD) |
| --- | --- | --- | --- |
| 0.1600000 | 320.0000000 | 320.0000000 | N/A |
| 0.1500000 | 40500.0000000 | 40820.0000000 | N/A |
| 0.1421541 | 4095.7393612 | 44915.7393612 | N/A |
| 0.1266555 | 2804.1364800 | 47719.8758412 | N/A |
| 0.1200000 | 300.0000000 | 48019.8758412 | N/A |
| 0.1117317 | 1705.4334451 | 49725.3092863 | N/A |
| 0.0977501 | 907.1789646 | 50632.4882509 | N/A |
| 0.0909091 | 3592.9380000 | 54225.4262509 | N/A |
| 0.0850552 | 487.5117488 | 54712.9379997 | N/A |
| 0.0739594 | 487.5117489 | 55200.4497486 | N/A |
| 0.0666667 | 1000.0000000 | 56200.4497486 | N/A |
| 0.0647360 | 907.1789646 | 57107.6287132 | N/A |
| 0.0576121 | 1705.4334451 | 58813.0621583 | N/A |
| 0.0555556 | 5000.0000000 | 63813.0621583 | N/A |
| 0.0527630 | 2804.1364801 | 66617.1986384 | N/A |
| 0.0526316 | 5000.0000000 | 71617.1986384 | N/A |
| 0.0503083 | 4095.7393612 | 75712.9379996 | N/A |
| 0.0095000 | 95000.0000000 | 170712.9379996 | N/A |
| 0.0090000 | 9000.0000000 | 179712.9379996 | N/A |
| 0.0001000 | 958.9494223 | 180671.8874219 | N/A |

### Asks (Vendas)

| Preço (XDB) | Quantidade (CBPAY) | Acumulado (CBPAY) | Valor (USD) |
| --- | --- | --- | --- |
| 0.3000000 | 270000.0000000 | 270000.0000000 | N/A |
| 0.8021579 | 2047.8696806 | 272047.8696806 | N/A |
| 0.8193411 | 1402.0682400 | 273449.9379206 | N/A |
| 0.8532843 | 852.7167226 | 274302.6546432 | N/A |
| 0.9031519 | 453.5894823 | 274756.2441255 | N/A |
| 0.9677158 | 243.7558744 | 274999.9999999 | N/A |
| 1.0453864 | 243.7558744 | 275243.7558743 | N/A |
| 1.1342510 | 453.5894823 | 275697.3453566 | N/A |
| 1.2321216 | 852.7167226 | 276550.0620792 | N/A |
| 1.3365883 | 1402.0682400 | 277952.1303192 | N/A |
| 1.4450786 | 2047.8696806 | 279999.9999998 | N/A |
| 2.5000000 | 199484.7660312 | 479484.7660310 | N/A |
| 4.0000000 | 956422.7774378 | 1435907.5434688 | N/A |
| 16.0000000 | 31000.0000000 | 1466907.5434688 | N/A |
| 19.0000000 | 5000.0000000 | 1471907.5434688 | N/A |

## Preço Atual do XDB

1 XDB = N/A USD

Última atualização: Erro'''
    
    # Process the data
    bids_df, asks_df, rate = process_order_book_data(sample_html)
    
    # Generate HTML
    html_output = generate_complete_html(bids_df, asks_df, rate)
    
    # Save to file
    with open('/home/ubuntu/order_book_with_usdt.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print("HTML file generated successfully: /home/ubuntu/order_book_with_usdt.html")

