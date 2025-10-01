"""
REST API client for Binance Futures with rate limiting
"""

import time
from typing import Dict, List, Optional

import requests
from threading import Lock

from ..monitoring.logger import get_logger


logger = get_logger('rest_client')


class BinanceRestClient:
    """REST API client with connection pooling and rate limiting"""
    
    BASE_URL = "https://fapi.binance.com/fapi/v1"
    
    def __init__(self, rate_limit: int = 1200):
        """
        Initialize REST client
        
        Args:
            rate_limit: Maximum requests per minute
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.request_times: List[float] = []
        self.lock = Lock()
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            # Wait if at limit
            if len(self.request_times) >= self.rate_limit:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    logger.warning(
                        'rate_limit_hit',
                        f'Rate limit hit, sleeping for {sleep_time:.2f}s'
                    )
                    time.sleep(sleep_time)
            
            self.request_times.append(time.time())
    
    def get_24hr_tickers(self) -> List[Dict]:
        """
        Fetch 24hr ticker data for all symbols
        
        Returns:
            List of ticker data dictionaries
        """
        self._check_rate_limit()
        
        try:
            url = f"{self.BASE_URL}/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            logger.debug('tickers_fetched', f'Fetched {len(response.json())} tickers')
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error('ticker_fetch_failed', str(e))
            return []
    
    def get_exchange_info(self) -> Dict:
        """
        Fetch exchange information
        
        Returns:
            Exchange info dictionary
        """
        self._check_rate_limit()
        
        try:
            url = f"{self.BASE_URL}/exchangeInfo"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(
                'exchange_info_fetched',
                f'Fetched info for {len(data.get("symbols", []))} symbols'
            )
            return data
        except requests.exceptions.RequestException as e:
            logger.error('exchange_info_fetch_failed', str(e))
            return {}
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int
    ) -> Optional[List[List]]:
        """
        Fetch candlestick data for a symbol
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (e.g., "15m")
            limit: Number of klines to fetch
            
        Returns:
            List of kline data or None on error
        """
        self._check_rate_limit()
        
        try:
            url = f"{self.BASE_URL}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error response
            if isinstance(data, dict) and 'code' in data:
                logger.error(
                    'klines_api_error',
                    f"API Error for {symbol}",
                    data={'error': data.get('msg')}
                )
                return None
            
            logger.debug('klines_fetched', f'Fetched {len(data)} klines for {symbol}')
            return data
        except requests.exceptions.RequestException as e:
            logger.error(
                'klines_fetch_failed',
                f'Failed to fetch klines for {symbol}',
                data={'error': str(e)}
            )
            return None
    
    def close(self) -> None:
        """Close the session"""
        self.session.close()
