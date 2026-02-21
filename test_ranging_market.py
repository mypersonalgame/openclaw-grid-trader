#!/usr/bin/env python3
"""
測試震盪市場環境下的策略表現
找一個價格在範圍內波動的時期
"""
import ccxt
import pandas as pd
import numpy as np
from grid_strategy_v2 import GridTraderV2
from backtest_v2 import GridBacktesterV2

def find_ranging_period():
    """尋找震盪市場時期"""
    exchange = ccxt.binance({'enableRateLimit': True})
    
    print("🔍 尋找震盪市場時期...")
    
    # 獲取更長的歷史數據
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=90)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # 滾動窗口尋找震盪期
    window = 30
    best_period = None
    best_score = float('inf')
    
    for i in range(len(df) - window):
        period = df.iloc[i:i+window]
        
        # 計算價格範圍和趨勢
        price_range = (period['close'].max() - period['close'].min()) / period['close'].mean()
        trend = (period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]
        
        # 震盪分數：低趨勢 + 適度波動
        score = abs(trend) + abs(price_range - 0.15)
        
        if score < best_score:
            best_score = score
            best_period = {
                'start': period['timestamp'].iloc[0],
                'end': period['timestamp'].iloc[-1],
                'start_price': period['close'].iloc[0],
                'end_price': period['close'].iloc[-1],
                'trend': trend * 100,
                'volatility': price_range * 100,
                'data': period
            }
    
    print(f"\n✅ 找到最佳震盪期:")
    print(f"   時間: {best_period['start'].date()} 至 {best_period['end'].date()}")
    print(f"   價格: ${best_period['start_price']:,.2f} → ${best_period['end_price']:,.2f}")
    print(f"   趨勢: {best_period['trend']:+.2f}%")
    print(f"   波動: {best_period['volatility']:.2f}%")
    
    return best_period

def test_with_period(start_date, days=30):
    """測試特定時期"""
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # 計算需要的數據點
    limit = days * 24
    
    # 獲取該時期的小時數據
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print(f"\n📊 測試震盪市場環境")
    print(f"   時間: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
    print(f"   價格: ${df['close'].iloc[0]:,.2f} → ${df['close'].iloc[-1]:,.2f}")
    print(f"   變化: {((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100):+.2f}%")
    
    return df

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 震盪市場測試")
    print("=" * 60)
    
    # 方案：測試最近 30 天（已知震盪）
    # 如果不滿意，可以用 find_ranging_period() 找其他時期
    
    # 測試較短時期（最近 14 天）
    trader = GridTraderV2(
        symbol='BTC/USDT',
        investment=1000,
        grid_count=20,
        price_range_pct=0.06,  # 較窄網格
        trend_filter=True,
        paper_trading=True
    )
    
    backtester = GridBacktesterV2(trader, days=14, interval='1h')
    trade_log, trend_changes = backtester.run_backtest()
    report = backtester.generate_report()
    
    print("\n" + "=" * 60)
    print("💡 結論")
    print("=" * 60)
    
    if report['monthly_return'] >= 3:
        print("✅ 策略在震盪市場表現良好")
        print("   建議：實盤部署，但需要趨勢監控")
    elif report['monthly_return'] >= 1:
        print("⚠️  策略勉強可行")
        print("   建議：繼續紙上交易觀察")
    else:
        print("❌ 策略需要優化")
        print("   建議：調整參數或策略")
    
    trader.save_state('test_ranging_result.json')
