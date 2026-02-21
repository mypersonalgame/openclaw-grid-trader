#!/usr/bin/env python3
"""測試 Binance API 連接"""
import ccxt
import sys

def test_connection():
    """測試 Binance 連接並取得 BTC 價格"""
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
        })
        
        # 獲取 BTC/USDT 價格
        ticker = exchange.fetch_ticker('BTC/USDT')
        
        print(f"✅ Binance 連接成功")
        print(f"📈 BTC/USDT 價格: ${ticker['last']:,.2f}")
        print(f"📊 24h 變化: {ticker['percentage']:.2f}%")
        print(f"📉 24h 最高: ${ticker['high']:,.2f}")
        print(f"📈 24h 最低: ${ticker['low']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
