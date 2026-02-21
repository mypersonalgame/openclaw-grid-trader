#!/usr/bin/env python3
"""
網格交易回測引擎 V2 - 支持趨勢過濾
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from grid_strategy_v2 import GridTraderV2

class GridBacktesterV2:
    """網格交易回測器 V2"""
    
    def __init__(self, trader, days=30, interval='1h'):
        self.trader = trader
        self.days = days
        self.interval = interval
        self.historical_data = None
        
    def fetch_historical_data(self):
        """獲取歷史數據"""
        print(f"📥 正在獲取 {self.days} 天的歷史數據...")
        
        if self.interval == '1h':
            limit = self.days * 24
        elif self.interval == '1d':
            limit = self.days
        else:
            limit = min(1000, self.days * 288)
        
        ohlcv = self.trader.exchange.fetch_ohlcv(
            self.trader.symbol, 
            self.interval, 
            limit=limit
        )
        
        df = pd.DataFrame(
            ohlcv, 
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        self.historical_data = df
        
        print(f"✅ 獲取 {len(df)} 個數據點")
        print(f"   時間範圍: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
        print(f"   價格範圍: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")
        
        return df
    
    def run_backtest(self):
        """執行回測"""
        if self.historical_data is None:
            self.fetch_historical_data()
        
        df = self.historical_data
        
        print("\n" + "=" * 60)
        print("🔄 開始回測（趨勢過濾版）...")
        print("=" * 60)
        
        # 初始化
        first_price = df.iloc[0]['close']
        self.trader.current_price = first_price
        self.trader.base_price = first_price
        
        # 動態調整網格範圍
        price_min = df['close'].min()
        price_max = df['close'].max()
        price_range = price_max - price_min
        
        lower_bound = price_min - price_range * 0.05
        upper_bound = price_max + price_range * 0.05
        
        self.trader.grids = np.linspace(lower_bound, upper_bound, self.trader.grid_count + 1)
        
        print(f"網格範圍: ${lower_bound:,.2f} - ${upper_bound:,.2f}")
        
        # 模擬交易
        trade_log = []
        trend_changes = []
        
        for idx, row in df.iterrows():
            current_price = row['close']
            
            # 更新趨勢（使用截至當前的歷史數據）
            if idx >= 25:  # 需要至少 25 個數據點
                price_history = df.iloc[:idx+1]['close'].values
                old_trend = self.trader.trend
                self.trader.trend = self.trader.calculate_trend(price_history)
                
                if old_trend != self.trader.trend:
                    trend_changes.append({
                        'timestamp': row['timestamp'],
                        'from': old_trend,
                        'to': self.trader.trend,
                        'price': current_price
                    })
                    print(f"\n  📊 趨勢變化 @ {row['timestamp']}: {old_trend} → {self.trader.trend} (${current_price:,.2f})")
            
            # 檢查網格信號
            signals = self.trader.check_grid_signals(current_price)
            
            # 執行交易
            for action, price, grid_index in signals:
                self.trader.execute_trade(action, price, grid_index)
                trade_log.append({
                    'timestamp': row['timestamp'],
                    'action': action,
                    'price': price,
                    'grid_index': grid_index,
                    'trend': self.trader.trend
                })
            
            self.trader.current_price = current_price
        
        print(f"\n✅ 回測完成！")
        print(f"   交易次數: {len(trade_log)}")
        print(f"   趨勢變化: {len(trend_changes)} 次")
        
        return trade_log, trend_changes
    
    def generate_report(self):
        """生成回測報告"""
        status = self.trader.get_status()
        df = self.historical_data
        
        total_days = (df['timestamp'].max() - df['timestamp'].min()).days
        if total_days == 0:
            total_days = 1
        
        monthly_return = (status['total_return_pct'] / total_days) * 30
        
        # 計算最大回撤
        equity_curve = [self.trader.investment]
        running_equity = self.trader.investment
        
        for trade in self.trader.filled_orders:
            running_equity += trade['profit']
            equity_curve.append(running_equity)
        
        peak = self.trader.investment
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = ((peak - equity) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # 趨勢統計
        trend_stats = {}
        for trade in self.trader.filled_orders:
            trend = trade.get('trend_at_entry', 'unknown')
            if trend not in trend_stats:
                trend_stats[trend] = {'count': 0, 'profit': 0, 'win': 0}
            trend_stats[trend]['count'] += 1
            trend_stats[trend]['profit'] += trade['profit']
            if trade['profit'] > 0:
                trend_stats[trend]['win'] += 1
        
        # 打印報告
        print("\n" + "=" * 60)
        print("📊 回測報告 V2（趨勢過濾版）")
        print("=" * 60)
        
        print(f"\n⏱️  回測期間:")
        print(f"   天數: {total_days} 天")
        print(f"   開始: {df['timestamp'].min()} | ${df['close'].iloc[0]:,.2f}")
        print(f"   結束: {df['timestamp'].max()} | ${df['close'].iloc[-1]:,.2f}")
        
        print(f"\n💰 資金狀況:")
        print(f"   初始資金: ${self.trader.investment:,.2f}")
        print(f"   最終資金: ${status['total_value']:,.2f}")
        print(f"   總盈虧: ${status['total_pnl']:,.2f}")
        print(f"   總回報率: {status['total_return_pct']:+.2f}%")
        print(f"   月化回報: {monthly_return:+.2f}%")
        print(f"   最大回撤: {max_drawdown:.2f}%")
        
        print(f"\n📈 交易統計:")
        print(f"   總交易次數: {status['total_trades']}")
        print(f"   已完成交易: {len(self.trader.filled_orders)}")
        print(f"   勝率: {status['win_rate']:.1f}%")
        if len(self.trader.filled_orders) > 0:
            print(f"   平均單筆利潤: ${status['realized_profit'] / len(self.trader.filled_orders):.2f}")
        
        print(f"\n🎯 趨勢表現:")
        for trend, stats in trend_stats.items():
            win_rate = (stats['win'] / stats['count'] * 100) if stats['count'] > 0 else 0
            print(f"   {trend.upper()}: {stats['count']} 筆 | 利潤: ${stats['profit']:.2f} | 勝率: {win_rate:.1f}%")
        
        print(f"\n📊 市場波動:")
        print(f"   價格變化: {((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100):+.2f}%")
        print(f"   波動率: {df['close'].std() / df['close'].mean() * 100:.2f}%")
        
        print("\n" + "=" * 60)
        
        # 判斷結果
        if monthly_return >= 3:
            print("✅ 策略表現優秀！月化回報達標 (≥3%)")
        elif monthly_return >= 1:
            print("⚠️  策略表現一般，建議繼續優化")
        else:
            print("❌ 策略表現不佳")
        
        # V2 改進評估
        print("\n💡 V2 改進效果:")
        if self.trader.trend_filter:
            print("   ✅ 趨勢過濾已啟用")
            down_trades = trend_stats.get('down', {'count': 0})
            print(f"   ✅ 下跌趨勢時開倉數: {down_trades['count']} 筆（應接近 0）")
        
        print("=" * 60)
        
        return {
            'total_return_pct': status['total_return_pct'],
            'monthly_return': monthly_return,
            'win_rate': status['win_rate'],
            'max_drawdown': max_drawdown,
            'total_trades': status['total_trades'],
            'trend_stats': trend_stats
        }

if __name__ == "__main__":
    print("🚀 網格交易策略 V2 回測（趨勢過濾版）")
    print("=" * 60)
    
    # 創建 V2 交易者
    trader = GridTraderV2(
        symbol='BTC/USDT',
        investment=1000,
        grid_count=20,
        price_range_pct=0.08,
        trend_filter=True,  # 啟用趨勢過濾
        paper_trading=True
    )
    
    # 創建回測器
    backtester = GridBacktesterV2(trader, days=30, interval='1h')
    
    # 執行回測
    trade_log, trend_changes = backtester.run_backtest()
    
    # 生成報告
    report = backtester.generate_report()
    
    # 保存結果
    trader.save_state('backtest_result_v2.json')
