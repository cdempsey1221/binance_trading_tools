import requests
import pandas as pd
from datetime import datetime
import asyncio
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1421238057843036382/yCYwKC-TAPxrQ4xf__n4_D3lqwd_nj2SaTjL5KcuxKwDJudbCk0vvkA-3_4gOzF7m37k"

async def send_alert(message):
    logging.info(f"Sending alert msg: {message}")
    payload = {
        "content": message
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        logging.info("Alert sent to Discord successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send alert to Discord: {e}")

# Function to get all Binance perpetual futures with liquidity filter
def get_binance_perps(min_avg_volume=1000):
    logging.info("Fetching Binance perpetuals with liquidity filter...")
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    response = requests.get(url).json()
    symbols = []
    for s in response:
        if s.get('symbol') and s.get('quoteVolume'):
            try:
                avg_volume = float(s['quoteVolume']) / 24
                if avg_volume >= min_avg_volume:
                    url_info = "https://fapi.binance.com/fapi/v1/exchangeInfo"
                    info = requests.get(url_info).json()
                    for sym in info['symbols']:
                        if sym['symbol'] == s['symbol'] and sym['contractType'] == 'PERPETUAL' and sym['status'] == 'TRADING':
                            symbols.append(s['symbol'])
                            break
            except Exception as e:
                logging.warning(f"Skipping symbol due to error: {s.get('symbol')} - {e}")
                continue
    logging.info(f"Found {len(symbols)} liquid perpetuals.")
    return symbols

# Function to check volume spikes
def check_volume_spikes(symbol, interval='1h', limit=9, threshold=150):
    logging.info(f"Checking ticker for volume spikes: {symbol}")
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url).json()
        if isinstance(data, dict) and data.get('code'):
            logging.error(f"API Error for {symbol}: {data['msg']}")
            return False, 0, None, f"Error: {data['msg']}"
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', *range(6,12)])
        df['volume'] = pd.to_numeric(df['volume'])
        avg_vol = df['volume'].iloc[:-1].mean()
        current_vol = df['volume'].iloc[-1]
        candle_time = df['timestamp'].iloc[-1]
        spike_pct = (current_vol / avg_vol - 1) * 100 if avg_vol > 0 else 0
        return spike_pct >= threshold, spike_pct, candle_time, None
    except Exception as e:
        logging.error(f"Exception during volume check for {symbol}: {e}")
        return False, 0, None, str(e)

# Track processed candles to avoid duplicate alerts
last_alerted = {}

# Main loop
async def main():
    symbols = get_binance_perps()
    logging.info(f"Scanning {len(symbols)} Binance perpetuals every 5 minutes...")
    while True:
        for symbol in symbols:
            url_24hr = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
            try:
                volume_24hr = float(requests.get(url_24hr).json()['quoteVolume']) / 24
                threshold = 150 if volume_24hr > 10000 else 250
            except Exception as e:
                logging.error(f"Could not get 24hr volume for {symbol}: {e}")
                continue

            spike_detected, spike_pct, candle_time, error = check_volume_spikes(symbol, threshold=threshold)
            if error:
                continue

            if spike_detected:
                if symbol not in last_alerted or last_alerted[symbol] != candle_time:
                    message = f"🚨 **VOLUME SPIKE ALERT** 🚨\n**{symbol}** has a **{spike_pct:.2f}%** volume spike!\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    logging.warning(message)
                    await send_alert(message)
                    last_alerted[symbol] = candle_time
        logging.info(f"Scan completed. Waiting 5 minutes...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
