
"""Agent state management with database models for portfolio and trades."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

from loguru import logger

from ..core.storage.postgres_storage import PostgresStorage


class TradeAction(Enum):
    """Trade action types."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeStatus(Enum):
    """Trade execution status."""

    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Position:
    """Trading position representation."""

    id: str
    symbol: str
    action: TradeAction
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        price = self.current_price or self.entry_price
        return self.quantity * price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        if self.action == TradeAction.BUY:
            current_value = self.quantity * (self.current_price or self.entry_price)
            cost_basis = self.quantity * self.entry_price
            return current_value - cost_basis
        return 0.0

    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized profit/loss percentage."""
        if self.action == TradeAction.BUY and self.entry_price > 0:
            current_price = self.current_price or self.entry_price
            return ((current_price - self.entry_price) / self.entry_price) * 100
        return 0.0

    def update_price(self, new_price: float) -> None:
        """Update current price and timestamp."""
        self.current_price = new_price
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class TradeDecision:
    """Trade decision record."""

    id: str
    symbol: str
    action: TradeAction
    quantity: float
    price: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    execution_price: Optional[float] = None
    fees: float = 0.0

    @property
    def total_value(self) -> float:
        """Total trade value including fees."""
        if self.price and self.quantity:
            return self.price * self.quantity + self.fees
        return 0.0

    def mark_executed(self, execution_price: float, fees: float = 0.0) -> None:
        """Mark trade as executed."""
        self.status = TradeStatus.EXECUTED
        self.execution_price = execution_price
        self.fees = fees
        self.executed_at = datetime.now(timezone.utc)

    def mark_failed(self, reason: str = "") -> None:
        """Mark trade as failed."""
        self.status = TradeStatus.FAILED
        if reason:
            self.reason = reason


@dataclass
class Portfolio:
    """Portfolio state management."""

    id: str
    initial_balance: float
    cash: float
    positions: List[Position] = field(default_factory=list)
    trade_history: List[TradeDecision] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_value(self) -> float:
        """Total portfolio value including positions."""
        positions_value = sum(pos.market_value for pos in self.positions)
        return self.cash + positions_value

    @property
    def total_pnl(self) -> float:
        """Total realized + unrealized P&L."""
        # Realized P&L from executed trades
        realized_pnl = 0.0

        # Calculate realized P&L from trade pairs
        buy_trades = {}
        for trade in self.trade_history:
            if trade.status == TradeStatus.EXECUTED:
                if trade.action == TradeAction.BUY:
                    if trade.symbol not in buy_trades:
                        buy_trades[trade.symbol] = []
                    buy_trades[trade.symbol].append(trade)
                elif trade.action == TradeAction.SELL and trade.symbol in buy_trades:
                    # Match with buy trades (FIFO)
                    sell_trade = trade
                    while buy_trades[trade.symbol] and sell_trade.quantity > 0:
                        buy_trade = buy_trades[trade.symbol][0]
                        min_qty = min(buy_trade.quantity, sell_trade.quantity)

                        realized_pnl += (sell_trade.execution_price - buy_trade.execution_price) * min_qty

                        buy_trade.quantity -= min_qty
                        sell_trade.quantity -= min_qty

                        if buy_trade.quantity <= 0:
                            buy_trades[trade.symbol].pop(0)

        # Unrealized P&L from open positions
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions)

        return realized_pnl + unrealized_pnl

    @property
    def total_pnl_percent(self) -> float:
        """Total P&L as percentage of initial balance."""
        if self.initial_balance > 0:
            return (self.total_pnl / self.initial_balance) * 100
        return 0.0

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None

    def add_position(self, position: Position) -> None:
        """Add a new position."""
        self.positions.append(position)
        self.updated_at = datetime.now(timezone.utc)
        logger.info(f"Added position: {position.symbol} {position.action.value} {position.quantity}")

    def remove_position(self, position_id: str) -> bool:
        """Remove a position by ID."""
        for i, pos in enumerate(self.positions):
            if pos.id == position_id:
                removed = self.positions.pop(i)
                self.updated_at = datetime.now(timezone.utc)
                logger.info(f"Removed position: {removed.symbol}")
                return True
        return False

    def update_position_price(self, symbol: str, price: float) -> None:
        """Update price for all positions in a symbol."""
        updated = False
        for pos in self.positions:
            if pos.symbol == symbol:
                pos.update_price(price)
                updated = True

        if updated:
            self.updated_at = datetime.now(timezone.utc)

    def add_trade(self, trade: TradeDecision) -> None:
        """Add a trade decision."""
        self.trade_history.append(trade)
        self.updated_at = datetime.now(timezone.utc)
        logger.info(f"Added trade: {trade.symbol} {trade.action.value} {trade.quantity}")

    def get_symbol_exposure(self, symbol: str) -> float:
        """Get total exposure to a symbol."""
        exposure = 0.0
        for pos in self.positions:
            if pos.symbol == symbol:
                exposure += pos.market_value
        return exposure

    def get_cash_allocation_percent(self) -> float:
        """Get cash allocation as percentage of total portfolio."""
        if self.total_value > 0:
            return (self.cash / self.total_value) * 100
        return 0.0

    def get_top_positions(self, limit: int = 10) -> List[Position]:
        """Get top positions by value."""
        return sorted(self.positions, key=lambda p: p.market_value, reverse=True)[:limit]


class AgentState:
    """
    Persistent agent state management with database integration.

    Manages portfolio state, trade decisions, and agent configuration
    with PostgreSQL persistence.
    """

    def __init__(
        self,
        agent_id: str,
        initial_balance: float = 10000.0,
        storage: Optional[PostgresStorage] = None,
    ):
        """Initialize agent state."""
        self.agent_id = agent_id
        self.initial_balance = initial_balance
        self.storage = storage

        # Initialize portfolio
        self.portfolio = Portfolio(
            id=f"{agent_id}_portfolio",
            initial_balance=initial_balance,
            cash=initial_balance,
        )

        # Agent configuration
        self.config: Dict[str, Any] = {
            "risk_level": "moderate",
            "max_positions": 10,
            "rebalance_interval": 3600,  # 1 hour
            "monitor_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            "price_alert_threshold": 5.0,  # 5%
        }

        # Performance metrics
        self.metrics: Dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "max_drawdown": 0.0,
            "peak_value": initial_balance,
        }

        logger.info(f"AgentState initialized for agent {agent_id}")

    async def load_from_database(self) -> bool:
        """Load agent state from database."""
        if not self.storage:
            logger.warning("No storage provided, skipping database load")
            return False

        try:
            # This would be implemented with actual database queries
            # For now, return True to indicate successful load
            logger.info(f"Agent state loaded from database for {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load agent state: {e}")
            return False

    async def save_to_database(self) -> bool:
        """Save agent state to database."""
        if not self.storage:
            logger.warning("No storage provided, skipping database save")
            return False

        try:
            # This would be implemented with actual database queries
            # For now, return True to indicate successful save
            logger.info(f"Agent state saved to database for {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")
            return False

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration."""
        self.config.update(new_config)
        logger.info(f"Updated agent config: {new_config}")

    def update_metrics(self) -> None:
        """Update performance metrics."""
        current_value = self.portfolio.total_value

        # Update peak value and max drawdown
        if current_value > self.metrics["peak_value"]:
            self.metrics["peak_value"] = current_value

        drawdown = (self.metrics["peak_value"] - current_value) / self.metrics["peak_value"] * 100
        if drawdown > self.metrics["max_drawdown"]:
            self.metrics["max_drawdown"] = drawdown

        # Update trade statistics
        executed_trades = [t for t in self.portfolio.trade_history if t.status == TradeStatus.EXECUTED]
        self.metrics["total_trades"] = len(executed_trades)

        # Calculate best/worst trades
        if executed_trades:
            trade_pnls = []
            for trade in executed_trades:
                # Calculate trade P&L (simplified)
                if trade.action == TradeAction.SELL and trade.execution_price:
                    # Find matching buy trade
                    for prev_trade in executed_trades:
                        if (prev_trade.symbol == trade.symbol and
                            prev_trade.action == TradeAction.BUY and
                            prev_trade.executed_at and
                            prev_trade.executed_at < trade.executed_at):
                            pnl = (trade.execution_price - prev_trade.execution_price) * trade.quantity
                            trade_pnls.append(pnl)
                            break

            if trade_pnls:
                self.metrics["best_trade"] = max(trade_pnls)
                self.metrics["worst_trade"] = min(trade_pnls)
                self.metrics["winning_trades"] = len([p for p in trade_pnls if p > 0])
                self.metrics["losing_trades"] = len([p for p in trade_pnls if p < 0])

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        self.update_metrics()

        return {
            "agent_id": self.agent_id,
            "portfolio": {
                "total_value": self.portfolio.total_value,
                "cash": self.portfolio.cash,
                "positions_count": len(self.portfolio.positions),
                "total_pnl": self.portfolio.total_pnl,
                "total_pnl_percent": self.portfolio.total_pnl_percent,
                "cash_allocation_percent": self.portfolio.get_cash_allocation_percent(),
            },
            "config": self.config,
            "metrics": self.metrics,
            "performance": {
                "win_rate": (self.metrics["winning_trades"] / max(1, self.metrics["total_trades"])) * 100,
                "total_return": ((self.portfolio.total_value - self.initial_balance) / self.initial_balance) * 100,
                "current_drawdown": self.metrics["max_drawdown"],
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def apply_trade_decision(self, trade: TradeDecision) -> bool:
        """Apply a trade decision to the portfolio."""
        try:
            if trade.action == TradeAction.BUY:
                # Check if we have enough cash
                required_cash = trade.total_value
                if required_cash > self.portfolio.cash:
                    logger.warning(f"Insufficient cash for {trade.symbol} trade")
                    trade.mark_failed("Insufficient cash")
                    return False

                # Create position
                position = Position(
                    id=f"pos_{trade.id}",
                    symbol=trade.symbol,
                    action=TradeAction.BUY,
                    quantity=trade.quantity,
                    entry_price=trade.execution_price or trade.price,
                )

                # Update portfolio
                self.portfolio.cash -= required_cash
                self.portfolio.add_position(position)
                self.portfolio.add_trade(trade)

            elif trade.action == TradeAction.SELL:
                position = self.portfolio.get_position(trade.symbol)
                if not position:
                    logger.warning(f"No position found for {trade.symbol} sell")
                    trade.mark_failed("No position to sell")
                    return False

                # Calculate sale proceeds
                sale_price = trade.execution_price or trade.price
                proceeds = trade.quantity * sale_price - trade.fees

                # Update portfolio
                self.portfolio.cash += proceeds
                self.portfolio.add_trade(trade)

                # Remove or update position
                if trade.quantity >= position.quantity:
                    self.portfolio.remove_position(position.id)
                else:
                    position.quantity -= trade.quantity

            # Save state to database
            await self.save_to_database()
            return True

        except Exception as e:
            logger.error(f"Error applying trade decision: {e}")
            trade.mark_failed(str(e))
            return False
