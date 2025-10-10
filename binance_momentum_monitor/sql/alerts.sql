CREATE DATABASE momentum_signal_monitor;

CREATE TABLE IF NOT EXISTS alerts (
    -- Core identification
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(50) NOT NULL,
    candle_timestamp BIGINT NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    
    -- Volume metrics
    volume_spike_pct FLOAT,
    volume_building BOOLEAN,
    current_volume DOUBLE,
    avg_volume DOUBLE,
    
    -- Price metrics
    price_change_pct FLOAT,
    price_change_current_bar FLOAT,
    price_change_1hour FLOAT,
    price_change_2hour FLOAT,
    price_change_4hour FLOAT,
    
    -- Momentum analysis
    momentum_score INT,
    momentum_stage VARCHAR(50),
    
    -- Quality indicators
    trends_aligned BOOLEAN,
    volume_price_sync BOOLEAN,
    volatility FLOAT,
    current_price DECIMAL(20, 8), /* Using DECIMAL for precision */

    -- Score breakdown
    volume_score FLOAT,
    price_score FLOAT,
    trend_score FLOAT,
    quality_score FLOAT,
    volatility_score FLOAT,
    
    -- Optional fields (allow NULL)
    volume_zscore FLOAT NULL,
    signal_strength FLOAT NULL,
    atr_normalized_return FLOAT NULL,
    volume_spike_threshold FLOAT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure each alert is unique per candle
    UNIQUE(symbol, timeframe, candle_timestamp)
);