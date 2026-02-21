#!/usr/bin/env python3
"""
網格交易策略 V2 - 趨勢過濾版
Grid Trading Strategy V2 with Trend Filter
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json

class GridTraderV2:
    """網格交易機器人 V2（含趨勢過濾）"""
    
    def __init__(self, symbol='BTC/USDT', investment=1000, grid_count=20, 
                 price_range_pct=0.08, trend_filter=True, paper_trading=True):
        """
        初始化網格交易機器人
        
        Args:
            symbol: 交易對
            investment: 投入資金
            grid_count: 網格數量
            price_range_pct: 價格範圍百分比
            trend_filter: 是否啟用趨勢過濾
            paper_trading: 紙上交易模式
        """
        self.symbol = symbol
        self.investment = investment
        self.grid_count = grid_count
        self.price_range_pct = price_range_pct
        self.trend_filter = trend_filter
        self.paper_trading = paper_trading
        
        # 交易所
        self.exchange = ccxt.binance({'enableRateLimit': True})
        
        # 網格設置
        self.grids = []
        self.current_price = 0
        self.base_price = 0
        
        # 趨勢指標
        self.ma_short = 0  # 短期均線（7期）
        self.ma_long = 0   # 長期均線（25期）
        self.trend = 'neutral'  # 'up', 'down', 'neutral'
        
        # 持倉記錄
        self.positions = []
        self.filled_orders = []
        
        # 績效記錄
        self.total_profit = 0
        self.trade_count = 0
        self.win_count = 0
        
        # 風險控制
        self.max_drawdown = 0
        self.stop_loss_pct = 0.15  # 總資金止損 15%
        
    def calculate_trend(self, price_history):
        """
        計算趨勢
        
        Args:
            price_history: 價格歷史（DataFrame, list, 或 numpy array）
        
        Returns:
            str: 'up', 'down', 'neutral'
        """
        if len(price_history) < 25:
            return 'neutral'
        
        # 處理不同類型的輸入
        if isinstance(price_history, np.ndarray):
            prices = price_history
        elif isinstance(price_history, list):
            prices = price_history
        else:
            prices = price_history['close'].values
        
        # 計算短期和長期均線
        self.ma_short = np.mean(prices[-7:])
        self.ma_long = np.mean(prices[-25:])
        
        # 判斷趨勢
        diff_pct = ((self.ma_short - self.ma_long) / self.ma_long) * 100
        
        if diff_pct > 2:
            return 'up'
        elif diff_pct < -2:
            return 'down'
        else:
            return 'neutral'
    
    def should_open_position(self):
        """判斷是否可以開新倉"""
        if not self.trend_filter:
            return True
        
        # 下跌趨勢時不開新倉
        if self.trend == 'down':
            return False
        
        # 檢查止損
        status = self.get_status()
        if status['total_return_pct'] < -self.stop_loss_pct * 100:
            return False
        
        return True
    
    def initialize(self, price_history=None):
        """初始化網格"""
        # 獲取當前價格
        ticker = self.exchange.fetch_ticker(self.symbol)
        self.current_price = ticker['last']
        self.base_price = self.current_price
        
        # 計算趨勢（如果有歷史數據）
        if price_history is not None:
            self.trend = self.calculate_trend(price_history)
        
        # 計算網格
        lower_bound = self.base_price * (1 - self.price_range_pct)
        upper_bound = self.base_price * (1 + self.price_range_pct)
        self.grids = np.linspace(lower_bound, upper_bound, self.grid_count + 1)
        
        print("=" * 60)
        print(f"🤖 網格交易機器人 V2 初始化")
        print("=" * 60)
        print(f"交易對: {self.symbol}")
        print(f"當前價格: ${self.current_price:,.2f}")
        print(f"投入資金: ${self.investment:,.2f}")
        print(f"網格數量: {self.grid_count}")
        print(f"價格範圍: ${lower_bound:,.2f} - ${upper_bound:,.2f}")
        print(f"趨勢過濾: {'啟用' if self.trend_filter else '關閉'}")
        if self.trend_filter:
            print(f"當前趨勢: {self.trend.upper()}")
            if self.ma_short > 0:
                print(f"MA(7): ${self.ma_short:,.2f}")
                print(f"MA(25): ${self.ma_long:,.2f}")
        print(f"模式: {'紙上交易' if self.paper_trading else '實盤交易'}")
        print("=" * 60)
        
        return True
    
    def check_grid_signals(self, current_price):
        """檢查網格信號"""
        signals = []
        
        for i, grid_price in enumerate(self.grids):
            # 買入信號
            if current_price <= grid_price < self.current_price:
                existing = [p for p in self.positions if p['grid_index'] == i]
                if not existing and self.should_open_position():
                    signals.append(('buy', grid_price, i))
            
            # 賣出信號
            elif current_price >= grid_price > self.current_price:
                existing = [p for p in self.positions if p['grid_index'] == i - 1]
                if existing:
                    signals.append(('sell', grid_price, i))
        
        return signals
    
    def execute_trade(self, action, price, grid_index):
        """執行交易"""
        amount_per_grid = self.investment / self.grid_count
        quantity = amount_per_grid / price
        
        if action == 'buy':
            order = {
                'action': 'buy',
                'price': price,
                'quantity': quantity,
                'cost': amount_per_grid,
                'grid_index': grid_index,
                'timestamp': datetime.now().isoformat(),
                'trend_at_entry': self.trend
            }
            self.positions.append(order)
            self.trade_count += 1
            
            print(f"  ✅ BUY  Grid {grid_index}: {quantity:.6f} @ ${price:,.2f} [Trend: {self.trend}]")
            
        elif action == 'sell':
            buy_order = [p for p in self.positions if p['grid_index'] == grid_index - 1][0]
            sell_value = buy_order['quantity'] * price
            profit = sell_value - buy_order['cost']
            profit_pct = (profit / buy_order['cost']) * 100
            
            trade = {
                'buy_price': buy_order['price'],
                'sell_price': price,
                'quantity': buy_order['quantity'],
                'profit': profit,
                'profit_pct': profit_pct,
                'grid_index': grid_index,
                'timestamp': datetime.now().isoformat(),
                'trend_at_entry': buy_order.get('trend_at_entry', 'unknown'),
                'trend_at_exit': self.trend
            }
            self.filled_orders.append(trade)
            self.positions.remove(buy_order)
            
            self.total_profit += profit
            self.trade_count += 1
            if profit > 0:
                self.win_count += 1
            
            print(f"  ✅ SELL Grid {grid_index}: {buy_order['quantity']:.6f} @ ${price:,.2f} | 利潤: ${profit:.2f} ({profit_pct:+.2f}%)")
    
    def get_status(self):
        """獲取當前狀態"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        current_price = ticker['last']
        
        unrealized_pnl = 0
        for pos in self.positions:
            current_value = pos['quantity'] * current_price
            unrealized_pnl += (current_value - pos['cost'])
        
        cash = self.investment - sum(p['cost'] for p in self.positions)
        position_value = sum(p['quantity'] * current_price for p in self.positions)
        total_value = cash + position_value + self.total_profit
        total_return_pct = ((total_value - self.investment) / self.investment) * 100
        
        return {
            'current_price': current_price,
            'trend': self.trend,
            'ma_short': self.ma_short,
            'ma_long': self.ma_long,
            'total_trades': self.trade_count,
            'win_rate': (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0,
            'realized_profit': self.total_profit,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': self.total_profit + unrealized_pnl,
            'total_value': total_value,
            'total_return_pct': total_return_pct,
            'open_positions': len(self.positions)
        }
    
    def print_status(self):
        """打印狀態"""
        status = self.get_status()
        
        print("\n" + "=" * 60)
        print("📊 網格交易狀態 V2")
        print("=" * 60)
        print(f"當前價格: ${status['current_price']:,.2f}")
        print(f"當前趨勢: {status['trend'].upper()}")
        if status['ma_short'] > 0:
            print(f"MA(7): ${status['ma_short']:,.2f} | MA(25): ${status['ma_long']:,.2f}")
        print("-" * 60)
        print(f"總交易: {status['total_trades']} | 勝率: {status['win_rate']:.1f}%")
        print(f"已實現利潤: ${status['realized_profit']:.2f}")
        print(f"未實現盈虧: ${status['unrealized_pnl']:.2f}")
        print(f"總盈虧: ${status['total_pnl']:.2f}")
        print(f"總資產: ${status['total_value']:.2f}")
        print(f"總回報率: {status['total_return_pct']:+.2f}%")
        print(f"開放持倉: {status['open_positions']}")
        print("=" * 60)
    
    def save_state(self, filename='grid_state_v2.json'):
        """保存狀態"""
        state = {
            'version': 2,
            'symbol': self.symbol,
            'investment': self.investment,
            'trend': self.trend,
            'positions': self.positions,
            'filled_orders': self.filled_orders,
            'total_profit': self.total_profit,
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'last_update': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)

if __name__ == "__main__":
    trader = GridTraderV2(
        symbol='BTC/USDT',
        investment=1000,
        grid_count=20,
        price_range_pct=0.08,
        trend_filter=True,
        paper_trading=True
    )
    
    trader.initialize()
    trader.print_status()
