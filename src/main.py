import requests
from rich.console import Console
from rich.panel import Panel
import plotext as plt
from datetime import datetime
import os
import multiprocessing

width = os.get_terminal_size().columns
console = Console()
cryptos = ["bitcoin", "ethereum", "dogecoin", "solana", "cardano"]

def get_crypto_price(crypto):
    id_map = {
        "coingecko": {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "dogecoin": "dogecoin",
            "solana": "solana",
            "cardano": "cardano"
        },
        "coinpaprika": {
            "bitcoin": "btc-bitcoin",
            "ethereum": "eth-ethereum",
            "dogecoin": "doge-dogecoin",
            "solana": "sol-solana",
            "cardano": "ada-cardano"
        },
        "binance": {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "dogecoin": "DOGE",
            "solana": "SOL",
            "cardano": "ADA"
        }
    }

    api_sources = [
        ("coingecko", "https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"),
        ("coinpaprika", "https://api.coinpaprika.com/v1/tickers/{crypto}"),
        ("binance", "https://api.binance.com/api/v3/ticker/price?symbol={crypto}USDT")
    ]

    for source_name, api_url in api_sources:
        try:
            crypto_id = id_map[source_name][crypto]
            url = api_url.format(crypto=crypto_id)
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if source_name == "coingecko":
                    return data[crypto_id]["usd"]
                elif source_name == "coinpaprika":
                    return data["quotes"]["USD"]["price"]
                elif source_name == "binance":
                    return float(data["price"])

            console.print(f"[bold yellow]Advertencia: API fallida ({url})[/bold yellow]")

        except Exception as e:
            console.print(f"[bold red]Error en {source_name}: {e}[/bold red]")

    console.print("[bold red]No se pudo obtener el precio desde ninguna fuente.[/bold red]")
    return None

def get_crypto_history(crypto, days=7):
    id_map = {
        "coingecko": {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "dogecoin": "dogecoin",
            "solana": "solana",
            "cardano": "cardano"
        },
        "coinpaprika": {
            "bitcoin": "btc-bitcoin",
            "ethereum": "eth-ethereum",
            "dogecoin": "doge-dogecoin",
            "solana": "sol-solana",
            "cardano": "ada-cardano"
        },
        "alternative": {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "dogecoin": "dogecoin",
            "solana": "solana",
            "cardano": "cardano"
        }
    }

    api_sources = [
        ("coingecko", "https://api.coingecko.com/api/v3/coins/{crypto}/market_chart?vs_currency=usd&days={days}&interval=daily"),
        ("coinpaprika", "https://api.coinpaprika.com/v1/coins/{crypto}/ohlcv/historical?start={start}&end={end}"),
        ("alternative", "https://api.alternativecrypto.com/v1/history?crypto={crypto}&days={days}")
    ]

    from datetime import datetime, timedelta
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    for source_name, api_url in api_sources:
        try:
            crypto_id = id_map[source_name][crypto]

            if "{start}" in api_url and "{end}" in api_url:
                url = api_url.format(crypto=crypto_id, start=start_str, end=end_str)
            else:
                url = api_url.format(crypto=crypto_id, days=days)

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if "prices" in data:
                    historical_data = data["prices"]  # CoinGecko
                elif "ohlcv" in data:
                    historical_data = [[x["timestamp"], x["close"]] for x in data["ohlcv"]]  # CoinPaprika
                elif isinstance(data, list) and all("date" in x and "price" in x for x in data):
                    historical_data = [[datetime.strptime(x["date"], "%Y-%m-%d").timestamp() * 1000, x["price"]] for x in data] # "alternative"
                else:
                    continue

                dates = [datetime.fromtimestamp(p[0] / 1000).strftime("%d/%m/%Y") for p in historical_data]
                prices = [round(p[1], 2) for p in historical_data]
                return dates, prices

            console.print(f"[bold yellow]Advertencia: API fallida ({url})[/bold yellow]")

        except Exception as e:
            console.print(f"[bold red]Error en {source_name}: {e}[/bold red]")

    console.print("[bold red]No se pudo obtener el historial desde ninguna fuente.[/bold red]")
    return [], []

def calculate_moving_average(prices, window=3):
    return [None if i < window-1 else round(sum(prices[i-window+1:i+1])/window, 2) for i in range(len(prices))]

def show_price_table(crypto, price):
    os.system('cls' if os.name == 'nt' else 'clear')
    panel = Panel(f"[bold cyan]{crypto.capitalize()}[/bold cyan]\n[green]${price:,.2f} USD[/green]" if price else "[red]No disponible[/red]",
                  title="📈 Precio Actual", border_style="blue")
    console.print(panel)

def show_price_plot_process(dates, prices, moving_avg):
    plt.date_form("d/m/Y")
    plt.clear_figure()
    plt.title("Precio de la Criptomoneda - Últimos Días")
    plt.xlabel("Fecha")
    plt.ylabel("Precio USD")
    plt.plot_size(width - 0, 30)
    plt.grid(True)

    plt.plot(dates, prices, label="Precio Diario")
    plt.plot(dates, moving_avg, label=f"Promedio Móvil ({len(moving_avg)})", color="red")

    plt.show()

def interact_with_user():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        console.print("[bold magenta]Selecciona una criptomoneda para ver su precio y gráfico:[/bold magenta]", justify="center")

        console.print("\n" * (os.get_terminal_size().lines - 10))

        options = "  ".join([f"[bold green]{idx}. {crypto.capitalize()}[/bold green]" for idx, crypto in enumerate(cryptos, 1)])
        console.print(options)

        console.print("[bold red]6. Salir[/bold red]")

        console.print("\n" + "-" * width + "\n")

        try:
            selection = int(input(f"{console.render_str('Ingresa el número de la criptomoneda (1-5), o 6 para salir: ')}"))
            if selection == 6:
                console.print("\n[bold blue]¡Hasta luego![/bold blue]")
                break
            elif 1 <= selection <= len(cryptos):
                crypto = cryptos[selection - 1]
                console.print(f"\n[bold cyan]Has seleccionado {crypto.capitalize()}.[/bold cyan] Obteniendo datos...\n")
                price = get_crypto_price(crypto)
                show_price_table(crypto, price)

                dates, prices = get_crypto_history(crypto, days=7)
                moving_avg = calculate_moving_average(prices)

                plot_process = multiprocessing.Process(target=show_price_plot_process, args=(dates, prices, moving_avg))
                plot_process.start()
                plot_process.join()

                input("\n[bold green]Presiona Enter para continuar...[/bold green]\n")
            else:
                console.print("[bold red]Selección inválida, por favor ingresa un número válido.[/bold red]")
        except ValueError:
            console.print("[bold red]Por favor ingresa un número válido.[/bold red]")

if __name__ == "__main__":
    interact_with_user()
