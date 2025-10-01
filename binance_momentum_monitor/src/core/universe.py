"""
Symbol universe management with caching
"""

import time
from typing import Dict, List, Set

from .types import SymbolInfo
from ..data.rest_client import BinanceRestClient
from ..monitoring.logger import get_logger


logger = get_logger('universe')


class SymbolUniverse:
    """Manages the universe of tradeable symbols with caching"""
    
    def __init__(
        self,
        rest_client: BinanceRestClient,
        min_hourly_volume: float,
        cache_ttl: int = 3600
    ):
        """
        Initialize symbol universe
        
        Args:
            rest_client: REST API client
            min_hourly_volume: Minimum average hourly volume in USD
            cache_ttl: Cache time-to-live in seconds
        """
        self.rest_client = rest_client
        self.min_hourly_volume = min_hourly_volume
        self.cache_ttl = cache_ttl
        
        self.symbols: Dict[str, SymbolInfo] = {}
        self.liquid_symbols: Set[str] = set()
        self.last_update: float = 0
    
    def get_liquid_perpetuals(self, force_refresh: bool = False) -> List[str]:
        """
        Get all perpetual futures symbols that meet liquidity requirements
        
        Args:
            force_refresh: Force cache refresh
            
        Returns:
            List of symbol names that meet criteria
        """
        now = time.time()
        
        # Check cache
        if not force_refresh and self.liquid_symbols and (now - self.last_update) < self.cache_ttl:
            logger.debug(
                'cache_hit',
                f'Using cached symbols (age: {now - self.last_update:.0f}s)'
            )
            return list(self.liquid_symbols)
        
        logger.info('fetching_universe', f'Fetching perpetuals with min hourly volume ${self.min_hourly_volume}...')
        
        # Fetch data
        tickers = self.rest_client.get_24hr_tickers()
        if not tickers:
            logger.warning('no_tickers', 'No ticker data received')
            return list(self.liquid_symbols)  # Return cached if available
        
        exchange_info = self.rest_client.get_exchange_info()
        if not exchange_info:
            logger.warning('no_exchange_info', 'No exchange info received')
            return list(self.liquid_symbols)
        
        # Build lookup for perpetual contracts
        perpetual_symbols = {
            sym['symbol']: sym
            for sym in exchange_info.get('symbols', [])
            if sym.get('contractType') == 'PERPETUAL'
            and sym.get('status') == 'TRADING'
        }
        
        # Filter by liquidity
        new_liquid_symbols = set()
        new_symbols = {}
        
        for ticker in tickers:
            symbol = ticker.get('symbol')
            if not symbol or symbol not in perpetual_symbols:
                continue
            
            try:
                quote_volume = float(ticker.get('quoteVolume', 0))
                avg_hourly_volume = quote_volume / 24
                
                sym_info = SymbolInfo(
                    symbol=symbol,
                    contract_type='PERPETUAL',
                    status='TRADING',
                    avg_hourly_volume=avg_hourly_volume,
                    is_liquid=avg_hourly_volume >= self.min_hourly_volume
                )
                
                new_symbols[symbol] = sym_info
                
                if sym_info.is_liquid:
                    new_liquid_symbols.add(symbol)
                    
            except (ValueError, TypeError) as e:
                logger.warning(
                    'symbol_parsing_error',
                    f'Skipping {symbol}',
                    data={'error': str(e)}
                )
                continue
        
        # Update cache
        self.symbols = new_symbols
        self.liquid_symbols = new_liquid_symbols
        self.last_update = now
        
        logger.info(
            'universe_updated',
            f'Found {len(self.liquid_symbols)} liquid perpetuals',
            data={
                'total_perpetuals': len(perpetual_symbols),
                'liquid_count': len(self.liquid_symbols)
            }
        )
        
        return list(self.liquid_symbols)
    
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """
        Get info for a specific symbol
        
        Args:
            symbol: Symbol name
            
        Returns:
            SymbolInfo or None if not found
        """
        return self.symbols.get(symbol)
    
    def is_liquid(self, symbol: str) -> bool:
        """
        Check if a symbol meets liquidity requirements
        
        Args:
            symbol: Symbol name
            
        Returns:
            True if liquid, False otherwise
        """
        return symbol in self.liquid_symbols
