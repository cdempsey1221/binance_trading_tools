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
    
    -- EMA trend analysis (Stage 1: data collection)
    ema_21_daily DECIMAL(20, 8) NULL COMMENT '21-period EMA from daily timeframe',
    ema_50_daily DECIMAL(20, 8) NULL COMMENT '50-period EMA from daily timeframe',
    price_vs_ema_21 VARCHAR(20) NULL COMMENT 'Price position: above, below, at, or unknown',
    ema_trend_bias VARCHAR(20) DEFAULT 'neutral' COMMENT 'Trend bias: bullish, bearish, or neutral',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure each alert is unique per candle
    UNIQUE(symbol, timeframe, candle_timestamp)
);

-- Indexes for efficient querying
CREATE INDEX idx_alerts_symbol ON alerts(symbol);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_alerts_momentum_score ON alerts(momentum_score);
CREATE INDEX idx_alerts_ema_bias ON alerts(ema_trend_bias);
CREATE INDEX idx_alerts_price_vs_ema ON alerts(price_vs_ema_21);