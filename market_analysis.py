#!/usr/bin/env python3
"""分析市場狀況來決定策略"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_market():
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # 分析主流幣種
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    
    print("=" * 60)
    print("📊 市場狀況分析")
    print("=" * 60)
    
    volatilities = []
    trends = []
    
    for symbol in symbols:
        # 獲取過去7天的日線數據
        ohlcv = exchange.fetch_ohlcv(symbol, '1d', limit=30)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 計算波動率（最近7天）
        recent_closes = df['close'].tail(7)
        volatility = (recent_closes.std() / recent_closes.mean()) * 100
        volatilities.append(volatility)
        
        # 計算趨勢（7日 vs 30日均線）
        ma7 = df['close'].tail(7).mean()
        ma30 = df['close'].tail(30).mean()
        trend = ((ma7 - ma30) / ma30) * 100
        trends.append(trend)
        
        # 當前價格變化
        current = df['close'].iloc[-1]
        prev = df['close'].iloc[-2]
        change_24h = ((current - prev) / prev) * 100
        
        print(f"\n{symbol}")
        print(f"  當前價格: ${current:,.2f}")
        print(f"  24h 變化: {change_24h:+.2f}%")
        print(f"  7日波動率: {volatility:.2f}%")
        print(f"  趨勢 (7d vs 30d): {trend:+.2f}%")
    
    # 市場總結
    avg_volatility = np.mean(volatilities)
    avg_trend = np.mean(trends)
    
    print("\n" + "=" * 60)
    print("📈 市場總結")
    print("=" * 60)
    print(f"平均波動率: {avg_volatility:.2f}%")
    print(f"平均趨勢: {avg_trend:+.2f}%")
    
    # 策略建議
    print("\n" + "=" * 60)
    print("💡 策略建議")
    print("=" * 60)
    
    if avg_volatility > 5 and abs(avg_trend) > 3:
        if avg_trend > 0:
            print("✅ 趨勢跟隨 (A) - 強勢上漲趨勢，高波動")
            print("   理由: 明確上升趨勢 + 足夠波動空間")
            recommendation = "A"
        else:
            print("⚠️  趨勢跟隨需謹慎 - 下跌趨勢風險大")
            print("✅ 網格交易 (B) - 高波動但趨勢不明")
            print("   理由: 波動大但方向不明，適合來回吃價差")
            recommendation = "B"
    elif avg_volatility < 3:
        print("✅ 網格交易 (B) - 低波動震盪市")
        print("   理由: 波動小，適合網格穩定吃價差")
        recommendation = "B"
    else:
        print("✅ 混合策略 - 波動適中")
        print("   建議: 70% 網格 + 30% 趨勢")
        recommendation = "B"
    
    print(f"\n🎯 推薦: 方案 {recommendation}")
    
    return {
        'volatility': avg_volatility,
        'trend': avg_trend,
        'recommendation': recommendation
    }

if __name__ == "__main__":
    analyze_market()
