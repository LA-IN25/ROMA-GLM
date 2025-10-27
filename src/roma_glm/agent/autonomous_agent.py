"""Autonomous crypto trading agent orchestrator."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

from loguru import logger

from ..scheduler.task_scheduler import TaskScheduler
from ..monitor.market_monitor import MarketMonitor, MarketAlert
from ..decision.decision_engine import DecisionEngine, RiskLevel
from ..agent.agent_state import AgentState, TradeDecision, TradeAction, TradeStatus
from ..api.execution_service import ExecutionService


class AutonomousCryptoAgent:
    """
    Autonomous crypto trading agent orchestrator.

    Coordinates scheduler, market monitor, decision engine, and state management
    to provide autonomous trading capabilities.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        initial_balance: float = 10000.0,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        execution_service: Optional[ExecutionService] = None,
    ):
        """Initialize the autonomous agent."""
        self.agent_id = agent_id or f"agent_{uuid4().hex[:8]}"
        self.running = False
        self.startup_time = datetime.now(timezone.utc)

        # Initialize core components
        self.scheduler = TaskScheduler()
        self.market_monitor = MarketMonitor()
        self.decision_engine = DecisionEngine(
            risk_level=risk_level, initial_portfolio_value=initial_balance
        )
        self.agent_state = AgentState(
            agent_id=self.agent_id, initial_balance=initial_balance
        )
        self.execution_service = execution_service

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []

        logger.info(
            f"AutonomousCryptoAgent initialized: {self.agent_id} with {risk_level.value} risk level"
        )

    async def _run_periodic_market_analysis(self) -> None:
        """
        Scheduled task for periodic market analysis.

        This is called by the scheduler at regular intervals (e.g., every 5 minutes).
        """
        logger.info("🔄 Running periodic market analysis...")
        try:
            if not self.execution_service:
                logger.error("No execution service available for market analysis")
                return

            # Create execution for market analysis
            execution_id = await self.execution_service.start_execution(
                goal="Comprehensive cryptocurrency market analysis - identify trading opportunities, market trends, and risk factors",
                config_profile="crypto_agent",
                metadata={
                    "agent_id": self.agent_id,
                    "trigger": "scheduled_analysis",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(f"Started market analysis execution: {execution_id}")

            # Wait for completion with timeout
            timeout = 300  # 5 minutes
            for _ in range(timeout // 5):  # Check every 5 seconds
                execution = await self.execution_service.get_execution(execution_id)
                if execution and execution.status in ["completed", "failed"]:
                    break
                await asyncio.sleep(5)

            # Get results and feed to decision engine
            if execution and execution.status == "completed":
                await self._process_analysis_results(execution)
            else:
                logger.error(f"Market analysis failed or timed out: {execution_id}")

        except Exception as e:
            logger.error(f"Error in periodic market analysis: {e}")

    async def _process_analysis_results(self, execution) -> None:
        """Process market analysis results and generate trading signals."""
        try:
            # Extract analysis results from execution
            # This would depend on how the execution results are stored
            analysis_results = {
                "execution_id": execution.id,
                "goal": execution.goal,
                "status": execution.status,
                "metadata": execution.metadata or {},
                # Add actual results when execution service provides them
                "insights": [],
                "market_data": {},
            }

            logger.info("📊 Processing market analysis results...")

            # Generate trading signals from analysis
            signals = await self.decision_engine.evaluate_analysis_results(
                analysis_results
            )

            # Execute signals
            for signal in signals:
                await self._execute_trading_signal(signal)

            logger.info(f"✅ Processed {len(signals)} trading signals from analysis")

        except Exception as e:
            logger.error(f"Error processing analysis results: {e}")

    async def _on_market_alert(self, alert: MarketAlert) -> None:
        """Handle market alerts from the monitor."""
        logger.info(f"🚨 Market alert: {alert.alert_type.value} for {alert.symbol}")

        try:
            # Generate trading signal from alert
            signal = await self.decision_engine.evaluate_market_alert(
                alert, self.agent_state.portfolio
            )

            if signal:
                await self._execute_trading_signal(signal)
            else:
                logger.info(f"No action needed for alert: {alert.symbol}")

        except Exception as e:
            logger.error(f"Error handling market alert: {e}")

    async def _execute_trading_signal(self, signal) -> None:
        """Execute a trading signal."""
        try:
            logger.info(
                f"📈 Executing trading signal: {signal.action.value} {signal.symbol}"
            )

            # Create trade decision
            trade = TradeDecision(
                id=f"trade_{uuid4().hex[:8]}",
                symbol=signal.symbol,
                action=signal.action,
                quantity=signal.position_size or 0.0,
                price=signal.entry_price,
                reason=signal.reasoning,
                metadata={
                    "signal_strength": signal.signal_strength.value,
                    "confidence_score": signal.confidence_score,
                    "source": "autonomous_agent",
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                },
            )

            # Apply trade decision to portfolio
            success = await self.agent_state.apply_trade_decision(trade)

            if success:
                # Record trade in decision engine for risk management
                self.decision_engine.record_trade(trade)
                logger.info(f"✅ Trade executed: {trade.symbol} {trade.action.value}")
            else:
                logger.warning(f"❌ Trade failed: {trade.symbol} {trade.action.value}")

        except Exception as e:
            logger.error(f"Error executing trading signal: {e}")

    async def _run_portfolio_rebalancing(self) -> None:
        """Periodic portfolio rebalancing and risk assessment."""
        logger.info("⚖️ Running portfolio rebalancing...")
        try:
            # Check if portfolio needs rebalancing
            portfolio = self.agent_state.portfolio

            # Update current prices for all positions
            for position in portfolio.positions:
                current_price = await self.market_monitor.get_current_price(
                    position.symbol
                )
                if current_price:
                    portfolio.update_position_price(position.symbol, current_price)

            # Generate rebalancing signals (simplified)
            # In practice, this would be more sophisticated
            signals = []

            # Check for stop losses
            for position in portfolio.positions:
                if position.stop_loss and position.current_price:
                    if position.current_price <= position.stop_loss:
                        signal = type(
                            "Signal",
                            (),
                            {
                                "symbol": position.symbol,
                                "action": TradeAction.SELL,
                                "position_size": position.quantity,
                                "reasoning": f"Stop loss triggered at ${position.stop_loss}",
                                "confidence_score": 1.0,
                            },
                        )()
                        signals.append(signal)

            # Execute rebalancing signals
            for signal in signals:
                await self._execute_trading_signal(signal)

            logger.info(f"✅ Rebalancing completed: {len(signals)} trades executed")

        except Exception as e:
            logger.error(f"Error in portfolio rebalancing: {e}")

    async def _run_health_check(self) -> None:
        """Periodic health check of agent components."""
        try:
            logger.debug("🔍 Running agent health check...")

            # Check scheduler status
            scheduler_tasks = self.scheduler.list_tasks()
            logger.debug(f"Scheduler running {len(scheduler_tasks)} tasks")

            # Check monitor status
            monitor_status = self.market_monitor.get_monitoring_status()
            logger.debug(
                f"Monitor status: {monitor_status['running']}, symbols: {len(monitor_status['symbols'])}"
            )

            # Check decision engine risk status
            risk_status = self.decision_engine.get_risk_status()
            logger.debug(
                f"Risk status: {risk_status['risk_level']}, daily P&L: {risk_status['daily_pnl']}"
            )

            # Check agent state
            agent_status = self.agent_state.get_status()
            logger.debug(
                f"Portfolio value: ${agent_status['portfolio']['total_value']:.2f}"
            )

        except Exception as e:
            logger.error(f"Error in health check: {e}")

    def _setup_monitoring_symbols(self) -> None:
        """Setup symbols to monitor based on agent configuration."""
        symbols = self.agent_state.config.get("monitor_symbols", ["BTCUSDT", "ETHUSDT"])

        for symbol in symbols:
            self.market_monitor.add_symbol(symbol)

            # Set percentage threshold alerts
            threshold = self.agent_state.config.get("price_alert_threshold", 5.0)
            self.market_monitor.set_percentage_threshold(symbol, threshold)

        logger.info(f"📊 Setup monitoring for {len(symbols)} symbols: {symbols}")

    async def run_autonomously(self) -> None:
        """
        Main autonomous agent execution loop.

        This method runs the agent autonomously with:
        1. Scheduled periodic tasks (market analysis, rebalancing)
        2. Real-time market monitoring with alerts
        3. Continuous decision making and trade execution
        4. Health monitoring and state persistence
        """
        if self.running:
            logger.warning("Agent is already running")
            return

        logger.info(f"🚀 Starting autonomous agent: {self.agent_id}")
        self.running = True

        try:
            # Load state from database
            await self.agent_state.load_from_database()

            # Setup monitoring
            self._setup_monitoring_symbols()
            self.market_monitor.add_alert_callback(self._on_market_alert)

            # Start scheduler
            self.scheduler.start()

            # Schedule periodic tasks
            self.scheduler.schedule_interval(
                task_func=self._run_periodic_market_analysis,
                interval_seconds=300,  # Every 5 minutes
                task_id="market_analysis",
            )

            self.scheduler.schedule_interval(
                task_func=self._run_portfolio_rebalancing,
                interval_seconds=3600,  # Every hour
                task_id="portfolio_rebalancing",
            )

            self.scheduler.schedule_interval(
                task_func=self._run_health_check,
                interval_seconds=60,  # Every minute
                task_id="health_check",
            )

            # Start market monitor
            monitor_task = asyncio.create_task(self.market_monitor.run())
            self._background_tasks.append(monitor_task)

            logger.info("✅ Agent started successfully - entering main loop")

            # Main decision loop
            while self.running:
                try:
                    # Continuous decision making
                    # This could check for various conditions and make proactive decisions
                    await asyncio.sleep(30)  # Check every 30 seconds

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in main decision loop: {e}")
                    await asyncio.sleep(5)  # Brief pause before continuing

        except Exception as e:
            logger.error(f"Fatal error in autonomous agent: {e}")
        finally:
            await self.shutdown()

    async def stop(self) -> None:
        """Stop the autonomous agent."""
        logger.info("🛑 Stopping autonomous agent...")
        self.running = False

        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to finish
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

    async def shutdown(self) -> None:
        """Gracefully shutdown the agent and save state."""
        logger.info("🔄 Shutting down autonomous agent...")

        try:
            # Stop components
            await self.market_monitor.stop()
            await self.scheduler.shutdown()

            # Save final state to database
            await self.agent_state.save_to_database()

            # Log final status
            status = self.agent_state.get_status()
            logger.info(
                f"✅ Agent shutdown complete. Final portfolio value: ${status['portfolio']['total_value']:.2f}"
            )

        except Exception as e:
            logger.error(f"Error during agent shutdown: {e}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        status = {
            "agent_id": self.agent_id,
            "running": self.running,
            "startup_time": self.startup_time.isoformat(),
            "uptime_seconds": (
                datetime.now(timezone.utc) - self.startup_time
            ).total_seconds(),
        }

        # Add component statuses
        try:
            status["scheduler"] = {
                "running": self.scheduler.is_running(),
                "tasks": self.scheduler.list_tasks(),
            }
        except Exception as e:
            status["scheduler"] = {"error": str(e)}

        try:
            status["market_monitor"] = self.market_monitor.get_monitoring_status()
        except Exception as e:
            status["market_monitor"] = {"error": str(e)}

        try:
            status["decision_engine"] = self.decision_engine.get_risk_status()
        except Exception as e:
            status["decision_engine"] = {"error": str(e)}

        try:
            status["agent_state"] = self.agent_state.get_status()
        except Exception as e:
            status["agent_state"] = {"error": str(e)}

        return status

    async def force_trade(
        self,
        symbol: str,
        action: TradeAction,
        quantity: float,
        price: Optional[float] = None,
    ) -> bool:
        """Force execute a trade (for manual intervention)."""
        logger.info(f"🔧 Force trade: {action.value} {quantity} {symbol}")

        trade = TradeDecision(
            id=f"manual_{uuid4().hex[:8]}",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            reason="Manual intervention",
            metadata={"source": "manual_intervention"},
        )

        return await self.agent_state.apply_trade_decision(trade)
