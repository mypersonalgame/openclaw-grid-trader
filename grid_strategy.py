#!/usr/bin/env python3
"""
網格交易策略引擎
Grid Trading Strategy Engine
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class GridTrader:
    """網格交易機器人"""
    
    def __init__(self, symbol='BTC/USDT', investment=1000, grid_count=10, 
                 price_range_pct=0.1, paper_trading=True):
        """
        初始化網格交易機器人
        
        Args:
            symbol: 交易對 (例如 'BTC/USDT')
            investment: 投入資金 (USDT)
            grid_count: 網格數量
            price_range_pct: 價格範圍百分比 (0.1 = ±10%)
            paper_trading: 紙上交易模式
        """
        self.symbol = symbol
        self.investment = investment
        self.grid_count = grid_count
        self.price_range_pct = price_range_pct
        self.paper_trading = paper_trading
        
        # 初始化交易所
        self.exchange = ccxt.binance({'enableRateLimit': True})
        
        # 網格設置
        self.grids = []
        self.current_price = 0
        self.base_price = 0
        
        # 持倉記錄
        self.positions = []  # 已買入的訂單
        self.filled_orders = []  # 已完成的交易
        
        # 績效記錄
        self.total_profit = 0
        self.trade_count = 0
        self.win_count = 0
        
    def initialize(self):
        """初始化網格"""
        # 獲取當前價格
        ticker = self.exchange.fetch_ticker(self.symbol)
        self.current_price = ticker['last']
        self.base_price = self.current_price
        
        # 計算網格上下限
        lower_bound = self.base_price * (1 - self.price_range_pct)
        upper_bound = self.base_price * (1 + self.price_range_pct)
        
        # 生成網格線
        self.grids = np.linspace(lower_bound, upper_bound, self.grid_count + 1)
        
        # 每格投入金額
        amount_per_grid = self.investment / self.grid_count
        
        print("=" * 60)
        print(f"🤖 網格交易機器人初始化")
        print("=" * 60)
        print(f"交易對: {self.symbol}")
        print(f"當前價格: ${self.current_price:,.2f}")
        print(f"投入資金: ${self.investment:,.2f}")
        print(f"網格數量: {self.grid_count}")
        print(f"價格範圍: ${lower_bound:,.2f} - ${upper_bound:,.2f}")
        print(f"每格金額: ${amount_per_grid:,.2f}")
        print(f"模式: {'紙上交易' if self.paper_trading else '實盤交易'}")
        print("=" * 60)
        
        # 顯示網格
        print("\n📊 網格設置:")
        for i, price in enumerate(self.grids):
            status = "🔵" if price < self.current_price else "⚪"
            print(f"  Grid {i:2d}: ${price:,.2f} {status}")
        
        return True
    
    def check_grid_signals(self, current_price):
        """
        檢查網格信號
        
        Returns:
            list: [(action, price, grid_index), ...]
        """
        signals = []
        
        # 檢查每個網格線
        for i, grid_price in enumerate(self.grids):
            # 買入信號：價格跌破網格線，且該格還沒買入
            if current_price <= grid_price < self.current_price:
                # 檢查這個網格是否已有持倉
                existing = [p for p in self.positions if p['grid_index'] == i]
                if not existing:
                    signals.append(('buy', grid_price, i))
            
            # 賣出信號：價格突破網格線，且該格有持倉
            elif current_price >= grid_price > self.current_price:
                # 檢查這個網格是否有持倉
                existing = [p for p in self.positions if p['grid_index'] == i - 1]
                if existing:
                    signals.append(('sell', grid_price, i))
        
        return signals
    
    def execute_trade(self, action, price, grid_index):
        """執行交易（紙上交易）"""
        amount_per_grid = self.investment / self.grid_count
        quantity = amount_per_grid / price
        
        if action == 'buy':
            # 買入
            order = {
                'action': 'buy',
                'price': price,
                'quantity': quantity,
                'cost': amount_per_grid,
                'grid_index': grid_index,
                'timestamp': datetime.now().isoformat()
            }
            self.positions.append(order)
            self.trade_count += 1
            
            print(f"  ✅ BUY  Grid {grid_index}: {quantity:.6f} @ ${price:,.2f}")
            
        elif action == 'sell':
            # 賣出：找到對應的買入訂單
            buy_order = [p for p in self.positions if p['grid_index'] == grid_index - 1][0]
            sell_value = buy_order['quantity'] * price
            profit = sell_value - buy_order['cost']
            profit_pct = (profit / buy_order['cost']) * 100
            
            # 記錄交易
            trade = {
                'buy_price': buy_order['price'],
                'sell_price': price,
                'quantity': buy_order['quantity'],
                'profit': profit,
                'profit_pct': profit_pct,
                'grid_index': grid_index,
                'timestamp': datetime.now().isoformat()
            }
            self.filled_orders.append(trade)
            
            # 移除持倉
            self.positions.remove(buy_order)
            
            # 更新統計
            self.total_profit += profit
            self.trade_count += 1
            if profit > 0:
                self.win_count += 1
            
            print(f"  ✅ SELL Grid {grid_index}: {buy_order['quantity']:.6f} @ ${price:,.2f} | 利潤: ${profit:.2f} ({profit_pct:+.2f}%)")
    
    def get_status(self):
        """獲取當前狀態"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        current_price = ticker['last']
        
        # 計算未實現盈虧
        unrealized_pnl = 0
        for pos in self.positions:
            current_value = pos['quantity'] * current_price
            unrealized_pnl += (current_value - pos['cost'])
        
        # 總資產
        cash = self.investment - sum(p['cost'] for p in self.positions)
        position_value = sum(p['quantity'] * current_price for p in self.positions)
        total_value = cash + position_value + self.total_profit
        total_return_pct = ((total_value - self.investment) / self.investment) * 100
        
        status = {
            'current_price': current_price,
            'base_price': self.base_price,
            'price_change_pct': ((current_price - self.base_price) / self.base_price) * 100,
            'total_trades': self.trade_count,
            'win_rate': (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0,
            'realized_profit': self.total_profit,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': self.total_profit + unrealized_pnl,
            'cash': cash,
            'position_value': position_value,
            'total_value': total_value,
            'total_return_pct': total_return_pct,
            'open_positions': len(self.positions)
        }
        
        return status
    
    def print_status(self):
        """打印當前狀態"""
        status = self.get_status()
        
        print("\n" + "=" * 60)
        print("📊 網格交易狀態")
        print("=" * 60)
        print(f"當前價格: ${status['current_price']:,.2f} ({status['price_change_pct']:+.2f}%)")
        print(f"基準價格: ${status['base_price']:,.2f}")
        print("-" * 60)
        print(f"總交易次數: {status['total_trades']}")
        print(f"勝率: {status['win_rate']:.1f}%")
        print(f"已實現利潤: ${status['realized_profit']:.2f}")
        print(f"未實現盈虧: ${status['unrealized_pnl']:.2f}")
        print(f"總盈虧: ${status['total_pnl']:.2f}")
        print("-" * 60)
        print(f"現金: ${status['cash']:.2f}")
        print(f"持倉價值: ${status['position_value']:.2f}")
        print(f"總資產: ${status['total_value']:.2f}")
        print(f"總回報率: {status['total_return_pct']:+.2f}%")
        print(f"開放持倉: {status['open_positions']}")
        print("=" * 60)
    
    def save_state(self, filename='grid_state.json'):
        """保存狀態"""
        state = {
            'symbol': self.symbol,
            'investment': self.investment,
            'grid_count': self.grid_count,
            'base_price': self.base_price,
            'grids': self.grids.tolist(),
            'positions': self.positions,
            'filled_orders': self.filled_orders,
            'total_profit': self.total_profit,
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'last_update': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"✅ 狀態已保存到 {filename}")

if __name__ == "__main__":
    # 示例用法
    trader = GridTrader(
        symbol='BTC/USDT',
        investment=1000,
        grid_count=10,
        price_range_pct=0.05,  # ±5%
        paper_trading=True
    )
    
    trader.initialize()
    trader.print_status()
