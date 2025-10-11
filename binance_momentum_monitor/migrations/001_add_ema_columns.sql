-- ============================================================================
-- Migration Script: Add EMA Trend Columns to Existing alerts Table
-- ============================================================================
-- Date: 2025-10-10
-- Purpose: Add 21 and 50 EMA daily columns for Stage 1 EMA trend data collection
-- Author: GitHub Copilot
-- 
-- IMPORTANT: Run this on your production database to add columns to existing table
-- This is for EXISTING installations. New installations should use sql/alerts.sql
-- ============================================================================

USE momentum_signal_monitor;

-- Add EMA trend analysis columns
ALTER TABLE alerts 
ADD COLUMN ema_21_daily DECIMAL(20, 8) NULL COMMENT '21-period EMA from daily timeframe',
ADD COLUMN ema_50_daily DECIMAL(20, 8) NULL COMMENT '50-period EMA from daily timeframe',
ADD COLUMN price_vs_ema_21 VARCHAR(20) NULL COMMENT 'Price position: above, below, at, or unknown',
ADD COLUMN ema_trend_bias VARCHAR(20) DEFAULT 'neutral' COMMENT 'Trend bias: bullish, bearish, or neutral';

-- Add indexes for efficient EMA filtering
CREATE INDEX idx_alerts_ema_bias ON alerts(ema_trend_bias);
CREATE INDEX idx_alerts_price_vs_ema ON alerts(price_vs_ema_21);

-- Verify the changes
SELECT 
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'momentum_signal_monitor'
  AND TABLE_NAME = 'alerts'
  AND (COLUMN_NAME LIKE 'ema%' OR COLUMN_NAME LIKE 'price_vs_ema%')
ORDER BY ORDINAL_POSITION;

-- Show all indexes including new ones
SHOW INDEXES FROM alerts;

-- Check table structure
DESCRIBE alerts;

-- ============================================================================
-- Rollback Instructions (if needed)
-- ============================================================================
-- To rollback this migration:
-- 
-- ALTER TABLE alerts 
-- DROP COLUMN ema_21_daily,
-- DROP COLUMN ema_50_daily,
-- DROP COLUMN price_vs_ema_21,
-- DROP COLUMN ema_trend_bias;
-- 
-- DROP INDEX idx_alerts_ema_bias ON alerts;
-- DROP INDEX idx_alerts_price_vs_ema ON alerts;
-- ============================================================================
