-- Migration: Add TBQR (Taker Buy Quote Ratio) columns
-- Purpose: Capture buying pressure metrics for momentum analysis
-- Date: 2025-10-13

USE momentum_signal_monitor;

-- Add TBQR buying pressure analysis columns
ALTER TABLE alerts 
ADD COLUMN tbqr_current DECIMAL(10, 6) NULL COMMENT 'Current bar buy/sell ratio (0-1, >0.5 = bullish)' AFTER ema_trend_bias,
ADD COLUMN tbqr_zscore DECIMAL(10, 4) NULL COMMENT 'TBQR statistical significance vs 20-bar average' AFTER tbqr_current,
ADD COLUMN tbqr_delta DECIMAL(10, 6) NULL COMMENT 'TBQR change from 3-bar average (acceleration)' AFTER tbqr_zscore,
ADD COLUMN quote_volume_zscore DECIMAL(10, 4) NULL COMMENT 'USD participation level (quote volume z-score)' AFTER tbqr_delta;

-- Add indexes for TBQR analysis queries
CREATE INDEX idx_alerts_tbqr_current ON alerts(tbqr_current);
CREATE INDEX idx_alerts_tbqr_zscore ON alerts(tbqr_zscore);

-- Verify columns were added
SHOW COLUMNS FROM alerts LIKE 'tbqr%';
SHOW COLUMNS FROM alerts LIKE 'quote_volume_zscore';

-- ==============================================================================
-- ROLLBACK INSTRUCTIONS (if needed):
-- ==============================================================================
-- ALTER TABLE alerts DROP COLUMN tbqr_current;
-- ALTER TABLE alerts DROP COLUMN tbqr_zscore;
-- ALTER TABLE alerts DROP COLUMN tbqr_delta;
-- ALTER TABLE alerts DROP COLUMN quote_volume_zscore;
-- DROP INDEX idx_alerts_tbqr_current ON alerts;
-- DROP INDEX idx_alerts_tbqr_zscore ON alerts;
-- ==============================================================================

-- Sample queries to analyze TBQR data after deployment:
-- 
-- 1. Find signals with strong buying pressure (TBQR > 0.6):
-- SELECT symbol, momentum_score, tbqr_current, tbqr_zscore, current_price
-- FROM alerts 
-- WHERE tbqr_current > 0.6 
-- ORDER BY tbqr_zscore DESC LIMIT 20;
--
-- 2. Find signals with accelerating buying pressure:
-- SELECT symbol, momentum_score, tbqr_delta, tbqr_current, price_change_pct
-- FROM alerts 
-- WHERE tbqr_delta > 0.05 
-- ORDER BY tbqr_delta DESC LIMIT 20;
--
-- 3. Compare high momentum signals with/without strong TBQR:
-- SELECT 
--   CASE WHEN tbqr_current > 0.55 THEN 'Strong Buy Pressure' ELSE 'Weak Buy Pressure' END as buy_pressure,
--   COUNT(*) as signal_count,
--   AVG(momentum_score) as avg_score,
--   AVG(price_change_1hour) as avg_1h_change
-- FROM alerts 
-- WHERE momentum_score >= 8
-- GROUP BY buy_pressure;
