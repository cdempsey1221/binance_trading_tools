"""
Binance Perpetual Futures Momentum Alert System
Monitors volume spikes and price momentum for liquid perpetual contracts
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration parameters for the alert system"""
    discord_webhook_url: str
    scan_interval: int = 300  # 5 minutes in seconds
    candle_timeframe: str = "15m"
    volume_threshold: int = 150
    price_threshold: int = 5
    min_liquidity: int = 1000  # USD per hour
    alert_cooldown: int = 30  # minutes
    lookback_candles: int = 8
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            discord_webhook_url=os.getenv(
                'DISCORD_WEBHOOK_URL',
                "https://discord.com/api/webhooks/1421238057843036382/yCYwKC-TAPxrQ4xf__n4_D3lqwd_nj2SaTjL5KcuxKwDJudbCk0vvkA-3_4gOzF7m37k"
            ),
            scan_interval=int(os.getenv('SCAN_INTERVAL', '300')),
            candle_timeframe=os.getenv('CANDLE_TIMEFRAME', '15m'),
            volume_threshold=int(os.getenv('VOLUME_THRESHOLD', '150')),
            price_threshold=int(os.getenv('PRICE_THRESHOLD', '5')),
            min_liquidity=int(os.getenv('MIN_LIQUIDITY', '1000')),
            alert_cooldown=int(os.getenv('ALERT_COOLDOWN', '30')),
            lookback_candles=int(os.getenv('LOOKBACK_CANDLES', '8'))
        )


@dataclass
class MomentumSignal:
    """Data class for momentum signals"""
    symbol: str
    volume_spike_pct: float
    price_change_pct: float
    candle_timestamp: int
    timeframe: str


class AlertManager:
    """Manages alert cooldowns and duplicate prevention"""
    
    def __init__(self, cooldown_minutes: int):
        self.cooldown_minutes = cooldown_minutes
        self.last_alert_times: Dict[str, datetime] = {}
    
    def can_alert(self, symbol: str) -> bool:
        """Check if enough time has passed since last alert for this symbol"""
        if symbol not in self.last_alert_times:
            return True
        
        time_since_last = datetime.now() - self.last_alert_times[symbol]
        return time_since_last >= timedelta(minutes=self.cooldown_minutes)
    
    def record_alert(self, symbol: str) -> None:
        """Record that an alert was sent for this symbol"""
        self.last_alert_times[symbol] = datetime.now()


class BinanceAPI:
    """Wrapper for Binance API calls"""
    
    BASE_URL = "https://fapi.binance.com/fapi/v1"
    
    @staticmethod
    def get_24hr_tickers() -> List[Dict]:
        """Fetch 24hr ticker data for all symbols"""
        try:
            url = f"{BinanceAPI.BASE_URL}/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch 24hr tickers: {e}")
            return []
    
    @staticmethod
    def get_exchange_info() -> Dict:
        """Fetch exchange information"""
        try:
            url = f"{BinanceAPI.BASE_URL}/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch exchange info: {e}")
            return {}
    
    @staticmethod
    def get_klines(
        symbol: str,
        interval: str,
        limit: int
    ) -> Optional[List[List]]:
        """Fetch candlestick data for a symbol"""
        try:
            url = f"{BinanceAPI.BASE_URL}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error response
            if isinstance(data, dict) and 'code' in data:
                logger.error(f"API Error for {symbol}: {data.get('msg')}")
                return None
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch klines for {symbol}: {e}")
            return None


class SymbolFilter:
    """Filters symbols based on liquidity and contract type"""
    
    @staticmethod
    def get_liquid_perpetuals(min_hourly_volume: float) -> List[str]:
        """
        Get all perpetual futures symbols that meet liquidity requirements
        
        Args:
            min_hourly_volume: Minimum average hourly volume in USD
            
        Returns:
            List of symbol names that meet criteria
        """
        logger.info(f"Fetching perpetuals with min hourly volume ${min_hourly_volume}...")
        
        tickers = BinanceAPI.get_24hr_tickers()
        if not tickers:
            logger.warning("No ticker data received")
            return []
        
        exchange_info = BinanceAPI.get_exchange_info()
        if not exchange_info:
            logger.warning("No exchange info received")
            return []
        
        # Build lookup for perpetual contracts
        perpetual_symbols = {
            sym['symbol']
            for sym in exchange_info.get('symbols', [])
            if sym.get('contractType') == 'PERPETUAL'
            and sym.get('status') == 'TRADING'
        }
        
        liquid_symbols = []
        for ticker in tickers:
            symbol = ticker.get('symbol')
            if not symbol or symbol not in perpetual_symbols:
                continue
            
            try:
                quote_volume = float(ticker.get('quoteVolume', 0))
                avg_hourly_volume = quote_volume / 24
                
                if avg_hourly_volume >= min_hourly_volume:
                    liquid_symbols.append(symbol)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping {symbol} due to parsing error: {e}")
                continue
        
        logger.info(f"Found {len(liquid_symbols)} liquid perpetuals")
        return liquid_symbols


class MomentumDetector:
    """Detects momentum signals based on volume and price"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze_symbol(
        self,
        symbol: str,
        avg_24hr_volume: float
    ) -> Optional[MomentumSignal]:
        """
        Analyze a symbol for momentum signals
        
        Args:
            symbol: Trading pair symbol
            avg_24hr_volume: Average hourly volume over 24 hours
            
        Returns:
            MomentumSignal if both conditions met, None otherwise
        """
        # Determine dynamic threshold based on liquidity
        volume_threshold = (
            self.config.volume_threshold
            if avg_24hr_volume > 10000
            else 250
        )
        
        # Fetch candlestick data
        klines = BinanceAPI.get_klines(
            symbol,
            self.config.candle_timeframe,
            self.config.lookback_candles + 1
        )
        
        if not klines:
            return None
        
        # Parse into DataFrame
        df = pd.DataFrame(
            klines,
            columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume',
                'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        )
        
        # Convert to numeric types
        df['volume'] = pd.to_numeric(df['volume'])
        df['open'] = pd.to_numeric(df['open'])
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculate volume spike
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]
        
        if avg_volume == 0:
            return None
        
        volume_spike_pct = (current_volume / avg_volume - 1) * 100
        
        # Calculate price change
        open_price = df['open'].iloc[-1]
        close_price = df['close'].iloc[-1]
        
        if open_price == 0:
            return None
        
        price_change_pct = (close_price / open_price - 1) * 100
        
        # Check both conditions (FR8, FR9)
        volume_condition = volume_spike_pct >= volume_threshold
        price_condition = price_change_pct >= self.config.price_threshold
        
        if volume_condition and price_condition:
            return MomentumSignal(
                symbol=symbol,
                volume_spike_pct=volume_spike_pct,
                price_change_pct=price_change_pct,
                candle_timestamp=int(df['timestamp'].iloc[-1]),
                timeframe=self.config.candle_timeframe
            )
        
        return None


class DiscordNotifier:
    """Handles Discord webhook notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_alert(self, signal: MomentumSignal) -> bool:
        """
        Send momentum alert to Discord
        
        Args:
            signal: MomentumSignal containing alert data
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Format alert message (FR10, FR11)
        message = (
            f"🚨 **MOMENTUM ALERT** 🚨\n"
            f"**{signal.symbol}**\n"
            f"Volume: +{signal.volume_spike_pct:.1f}%\n"
            f"Price: +{signal.price_change_pct:.1f}%\n"
            f"Timeframe: {signal.timeframe}"
        )
        
        logger.info(f"Sending alert: {signal.symbol}")
        
        payload = {"content": message}
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Alert sent successfully for {signal.symbol}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send alert for {signal.symbol}: {e}")
            return False


class MomentumScanner:
    """Main scanner orchestrating the alert system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.alert_manager = AlertManager(config.alert_cooldown)
        self.momentum_detector = MomentumDetector(config)
        self.notifier = DiscordNotifier(config.discord_webhook_url)
        self.symbols: List[str] = []
    
    def initialize_symbols(self) -> None:
        """Fetch and cache liquid perpetual symbols"""
        self.symbols = SymbolFilter.get_liquid_perpetuals(
            self.config.min_liquidity
        )
        logger.info(f"Initialized with {len(self.symbols)} symbols")
    
    async def scan_symbol(self, symbol: str) -> None:
        """Scan a single symbol for momentum signals"""
        # Check cooldown (FR9, section 3.3)
        if not self.alert_manager.can_alert(symbol):
            return
        
        # Get current 24hr volume for dynamic thresholding
        try:
            tickers = BinanceAPI.get_24hr_tickers()
            ticker = next(
                (t for t in tickers if t.get('symbol') == symbol),
                None
            )
            if not ticker:
                return
            
            avg_hourly_volume = float(ticker.get('quoteVolume', 0)) / 24
        except (ValueError, TypeError, StopIteration):
            logger.warning(f"Could not get 24hr volume for {symbol}")
            return
        
        # Analyze for momentum
        signal = self.momentum_detector.analyze_symbol(
            symbol,
            avg_hourly_volume
        )
        
        if signal:
            success = await self.notifier.send_alert(signal)
            if success:
                self.alert_manager.record_alert(symbol)
    
    async def run_scan_cycle(self) -> None:
        """Execute one complete scan of all symbols"""
        logger.info(f"Starting scan cycle for {len(self.symbols)} symbols...")
        
        for symbol in self.symbols:
            await self.scan_symbol(symbol)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        logger.info("Scan cycle completed")
    
    async def run(self) -> None:
        """Main execution loop"""
        self.initialize_symbols()
        
        logger.info(
            f"Starting momentum scanner with {self.config.candle_timeframe} "
            f"timeframe, scanning every {self.config.scan_interval}s"
        )
        
        while True:
            try:
                await self.run_scan_cycle()
            except Exception as e:
                logger.error(f"Error in scan cycle: {e}", exc_info=True)
            
            logger.info(
                f"Waiting {self.config.scan_interval}s until next scan..."
            )
            await asyncio.sleep(self.config.scan_interval)


async def main() -> None:
    """Application entry point"""
    config = Config.from_env()
    scanner = MomentumScanner(config)
    await scanner.run()


if __name__ == "__main__":
    asyncio.run(main())
