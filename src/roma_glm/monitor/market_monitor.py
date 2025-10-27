"""Real-time market monitoring for autonomous trading agent."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import websockets
import httpx
from loguru import logger

from roma_glm.tools.crypto.binance.binance import BinanceToolkit
from roma_glm.tools.crypto.coingecko.coingecko import CoinGeckoToolkit


class AlertType(Enum):
    """Types of market alerts."""

    PRICE_CHANGE = "price_change"
    VOLUME_SPIKE = "volume_spike"
    PRICE_THRESHOLD = "price_threshold"
    TECHNICAL_SIGNAL = "technical_signal"


@dataclass
class MarketAlert:
    """Market alert data structure."""

    symbol: str
    alert_type: AlertType
    current_value: float
    threshold_value: float
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class PricePoint:
    """Single price data point."""

    symbol: str
    price: float
    volume: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class MarketMonitor:
    """
    Real-time market monitoring with websocket connections and alert system.

    Monitors cryptocurrency prices and triggers alerts based on configurable thresholds.
    """

    def __init__(self):
        """Initialize the market monitor."""
        self.running = False
        self._price_history: Dict[str, List[PricePoint]] = {}
        self._alert_callbacks: List[Callable[[MarketAlert], None]] = []
        self._price_thresholds: Dict[str, Dict[str, float]] = {}
        self._percentage_thresholds: Dict[str, float] = {}
        self._websocket_tasks: List[asyncio.Task] = []
        self._monitoring_symbols: set = set()

        # Initialize toolkits for data access
        self.binance_toolkit = BinanceToolkit()
        self.coingecko_toolkit = CoinGeckoToolkit()

        logger.info("MarketMonitor initialized")

    def add_alert_callback(self, callback: Callable[[MarketAlert], None]) -> None:
        """
        Add a callback function to handle market alerts.

        Args:
            callback: Function to call when alert is triggered
        """
        self._alert_callbacks.append(callback)
        logger.info(f"Added alert callback: {callback.__name__}")

    def remove_alert_callback(self, callback: Callable[[MarketAlert], None]) -> None:
        """
        Remove an alert callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
            logger.info(f"Removed alert callback: {callback.__name__}")

    def set_price_threshold(
        self, symbol: str, above: Optional[float] = None, below: Optional[float] = None
    ) -> None:
        """
        Set price threshold alerts for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            above: Alert when price goes above this value
            below: Alert when price goes below this value
        """
        if symbol not in self._price_thresholds:
            self._price_thresholds[symbol] = {}

        if above is not None:
            self._price_thresholds[symbol]["above"] = above
            logger.info(f"Set price alert for {symbol} above ${above}")

        if below is not None:
            self._price_thresholds[symbol]["below"] = below
            logger.info(f"Set price alert for {symbol} below ${below}")

    def set_percentage_threshold(self, symbol: str, percentage: float) -> None:
        """
        Set percentage change threshold for alerts.

        Args:
            symbol: Trading symbol
            percentage: Percentage change threshold (e.g., 5.0 for 5%)
        """
        self._percentage_thresholds[symbol] = percentage
        logger.info(f"Set {percentage}% threshold for {symbol}")

    def add_symbol(self, symbol: str) -> None:
        """
        Add a symbol to monitor.

        Args:
            symbol: Trading symbol to monitor
        """
        if symbol not in self._monitoring_symbols:
            self._monitoring_symbols.add(symbol)
            self._price_history[symbol] = []
            logger.info(f"Added {symbol} to monitoring list")

    def remove_symbol(self, symbol: str) -> None:
        """
        Remove a symbol from monitoring.

        Args:
            symbol: Trading symbol to stop monitoring
        """
        self._monitoring_symbols.discard(symbol)
        if symbol in self._price_history:
            del self._price_history[symbol]
        if symbol in self._price_thresholds:
            del self._price_thresholds[symbol]
        if symbol in self._percentage_thresholds:
            del self._percentage_thresholds[symbol]
        logger.info(f"Removed {symbol} from monitoring list")

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current price or None if unavailable
        """
        try:
            # Try Binance first for better real-time data
            ticker = await self.binance_toolkit.get_ticker_stats(symbol)
            if ticker and "last_price" in ticker:
                return float(ticker["last_price"])
        except Exception as e:
            logger.debug(f"Binance API failed for {symbol}: {e}")

        try:
            # Fallback to CoinGecko
            price_data = await self.coingecko_toolkit.get_simple_price(symbol.lower())
            if price_data and symbol.lower() in price_data:
                return float(price_data[symbol.lower()]["usd"])
        except Exception as e:
            logger.debug(f"CoinGecko API failed for {symbol}: {e}")

        return None

    async def _check_price_thresholds(self, symbol: str, current_price: float) -> None:
        """Check if price thresholds are triggered."""
        if symbol not in self._price_thresholds:
            return

        thresholds = self._price_thresholds[symbol]

        # Check above threshold
        if "above" in thresholds and current_price > thresholds["above"]:
            alert = MarketAlert(
                symbol=symbol,
                alert_type=AlertType.PRICE_THRESHOLD,
                current_value=current_price,
                threshold_value=thresholds["above"],
                timestamp=datetime.now(timezone.utc),
                metadata={"direction": "above"},
            )
            await self._trigger_alert(alert)

        # Check below threshold
        if "below" in thresholds and current_price < thresholds["below"]:
            alert = MarketAlert(
                symbol=symbol,
                alert_type=AlertType.PRICE_THRESHOLD,
                current_value=current_price,
                threshold_value=thresholds["below"],
                timestamp=datetime.now(timezone.utc),
                metadata={"direction": "below"},
            )
            await self._trigger_alert(alert)

    async def _check_percentage_changes(
        self, symbol: str, current_price: float
    ) -> None:
        """Check if percentage change threshold is triggered."""
        if symbol not in self._percentage_thresholds:
            return

        history = self._price_history.get(symbol, [])
        if len(history) < 2:
            return

        # Compare with previous price point
        previous_price = history[-1].price
        percentage_change = ((current_price - previous_price) / previous_price) * 100
        threshold = self._percentage_thresholds[symbol]

        if abs(percentage_change) >= threshold:
            alert = MarketAlert(
                symbol=symbol,
                alert_type=AlertType.PRICE_CHANGE,
                current_value=percentage_change,
                threshold_value=threshold,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "previous_price": previous_price,
                    "current_price": current_price,
                    "percentage_change": percentage_change,
                },
            )
            await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: MarketAlert) -> None:
        """Trigger alert to all registered callbacks."""
        logger.info(f"Triggering alert: {alert.alert_type.value} for {alert.symbol}")

        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback {callback.__name__}: {e}")

    async def _update_price_history(
        self, symbol: str, price: float, volume: Optional[float] = None
    ) -> None:
        """Update price history for a symbol."""
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        price_point = PricePoint(symbol=symbol, price=price, volume=volume)
        self._price_history[symbol].append(price_point)

        # Keep only last 1000 price points to prevent memory issues
        if len(self._price_history[symbol]) > 1000:
            self._price_history[symbol] = self._price_history[symbol][-1000:]

    async def _monitor_symbol(self, symbol: str, interval: int = 5) -> None:
        """
        Monitor a single symbol for price changes.

        Args:
            symbol: Trading symbol to monitor
            interval: Polling interval in seconds
        """
        logger.info(f"Starting monitoring for {symbol} every {interval}s")

        while self.running:
            try:
                current_price = await self.get_current_price(symbol)
                if current_price is not None:
                    await self._update_price_history(symbol, current_price)
                    await self._check_price_thresholds(symbol, current_price)
                    await self._check_percentage_changes(symbol, current_price)

            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")

            await asyncio.sleep(interval)

    async def run(
        self, alert_callback: Optional[Callable[[MarketAlert], None]] = None
    ) -> None:
        """
        Start the market monitor.

        Args:
            alert_callback: Optional default callback for alerts
        """
        if self.running:
            logger.warning("MarketMonitor is already running")
            return

        if alert_callback:
            self.add_alert_callback(alert_callback)

        self.running = True
        logger.info("Starting MarketMonitor...")

        # Start monitoring tasks for each symbol
        for symbol in self._monitoring_symbols:
            task = asyncio.create_task(self._monitor_symbol(symbol))
            self._websocket_tasks.append(task)

        # Wait for all monitoring tasks
        try:
            await asyncio.gather(*self._websocket_tasks)
        except asyncio.CancelledError:
            logger.info("MarketMonitor stopped")

    async def stop(self) -> None:
        """Stop the market monitor."""
        if not self.running:
            return

        logger.info("Stopping MarketMonitor...")
        self.running = False

        # Cancel all monitoring tasks
        for task in self._websocket_tasks:
            task.cancel()

        # Wait for tasks to finish
        if self._websocket_tasks:
            await asyncio.gather(*self._websocket_tasks, return_exceptions=True)

        self._websocket_tasks.clear()
        logger.info("MarketMonitor stopped")

    def get_price_history(
        self, symbol: str, limit: Optional[int] = None
    ) -> List[PricePoint]:
        """
        Get price history for a symbol.

        Args:
            symbol: Trading symbol
            limit: Maximum number of price points to return

        Returns:
            List of price points
        """
        history = self._price_history.get(symbol, [])
        if limit:
            return history[-limit:]
        return history

    def get_latest_price(self, symbol: str) -> Optional[PricePoint]:
        """
        Get the latest price point for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price point or None if no data
        """
        history = self._price_history.get(symbol, [])
        return history[-1] if history else None

    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.

        Returns:
            Dictionary with monitoring status
        """
        return {
            "running": self.running,
            "symbols": list(self._monitoring_symbols),
            "price_thresholds": self._price_thresholds,
            "percentage_thresholds": self._percentage_thresholds,
            "alert_callbacks_count": len(self._alert_callbacks),
            "price_history_sizes": {
                symbol: len(history) for symbol, history in self._price_history.items()
            },
        }
