# OpenClaw Grid Trader 🤖📊

AI-driven cryptocurrency grid trading bot powered by OpenClaw.

## 🎯 Strategy

**Grid Trading** - Automated buy-low-sell-high strategy optimized for sideways/ranging markets.

- **Target Return:** 3-5% per month
- **Risk Level:** Conservative
- **Capital:** $1,000-1,500 USD
- **Markets:** Crypto (Binance)

## 📁 Project Structure

```
trading/
├── test_binance.py      # Binance API connection test
├── market_analysis.py   # Market condition analysis
├── grid_strategy.py     # Grid trading strategy (coming soon)
└── backtest.py          # Backtesting engine (coming soon)
```

## 🚀 Setup

### Requirements

- Python 3.12+
- Virtual environment (included)

### Installation

```bash
# Create virtual environment
python3 -m venv trading_env

# Activate
source trading_env/bin/activate

# Install dependencies
pip install ccxt pandas numpy
```

### Test Connection

```bash
python test_binance.py
```

## 📊 Market Analysis

Analyze current market conditions:

```bash
python market_analysis.py
```

## 🛡️ Risk Management

- **Paper Trading First:** All strategies tested with simulated funds before live trading
- **Stop Loss:** Automatic position limits
- **Cost Control:** API usage monitored to stay within budget
- **No Secrets:** API keys stored locally (never committed)

## 💰 Cost Structure

- **VPS (Vultr):** $12/month
- **AI Model (Claude):** ~$5-10/month (monitoring only)
- **Exchange Fees:** ~0.1% per trade
- **Total Operating Cost:** ~$17-22/month

## 📝 Development Log

### 2026-02-21
- ✅ Environment setup complete
- ✅ Binance API tested successfully
- ✅ Market analysis tool created
- ✅ Strategy selected: Grid Trading (B)
- 🔄 Next: Build grid strategy engine

## 🤝 About

Built by **jj** (AI assistant) for James.

- **Agent:** OpenClaw AI
- **Model:** Claude Sonnet 4.5
- **Philosophy:** Precision over speed, safety over profit

---

**⚠️ Disclaimer:** Cryptocurrency trading carries risk. This bot is experimental. Never invest more than you can afford to lose.
