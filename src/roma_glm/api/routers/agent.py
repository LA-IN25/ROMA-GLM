"""Autonomous agent management endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from roma_glm.api.schemas import (
    ErrorResponse,
    SuccessResponse,
    AgentStatusResponse,
    AgentConfigRequest,
    ManualTradeRequest,
)
from roma_glm.api.dependencies import get_app_state
from roma_glm.agent.autonomous_agent import AutonomousCryptoAgent
from roma_glm.decision.decision_engine import RiskLevel

router = APIRouter()


@router.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status(request: Request) -> AgentStatusResponse:
    """
    Get autonomous agent status.

    Returns comprehensive status including:
    - Agent runtime state
    - Portfolio performance
    - Scheduled tasks
    - Market monitoring status
    - Risk management metrics
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        status = app_state.autonomous_agent.get_agent_status()
        return AgentStatusResponse(
            success=True, data=status, timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/agent/start", response_model=SuccessResponse)
async def start_agent(request: Request) -> SuccessResponse:
    """
    Start the autonomous agent.

    This will start the autonomous trading loop if it's not already running.
    The agent will:
    - Begin monitoring configured symbols
    - Schedule periodic market analysis
    - Execute trading decisions based on alerts and analysis
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        if app_state.autonomous_agent.running:
            return SuccessResponse(
                success=True,
                message="Autonomous Agent is already running",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        import asyncio

        asyncio.create_task(app_state.autonomous_agent.run_autonomously())

        logger.info("Autonomous Agent started via API")
        return SuccessResponse(
            success=True,
            message="Autonomous Agent started successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")


@router.post("/agent/stop", response_model=SuccessResponse)
async def stop_agent(request: Request) -> SuccessResponse:
    """
    Stop the autonomous agent.

    This will gracefully stop the autonomous trading loop.
    The agent will:
    - Complete any pending trades
    - Stop monitoring markets
    - Cancel scheduled tasks
    - Save final state to database
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        if not app_state.autonomous_agent.running:
            return SuccessResponse(
                success=True,
                message="Autonomous Agent is already stopped",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        await app_state.autonomous_agent.stop()

        logger.info("Autonomous Agent stopped via API")
        return SuccessResponse(
            success=True,
            message="Autonomous Agent stopped successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to stop agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {str(e)}")


@router.post("/agent/config", response_model=SuccessResponse)
async def update_agent_config(
    request: Request, config: AgentConfigRequest
) -> SuccessResponse:
    """
    Update autonomous agent configuration.

    Allows updating:
    - Risk level (conservative, moderate, aggressive)
    - Monitor symbols list
    - Alert thresholds
    - Rebalancing intervals
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        agent = app_state.autonomous_agent

        # Update risk level if provided
        if config.risk_level:
            try:
                new_risk_level = RiskLevel(config.risk_level.lower())
                agent.decision_engine.update_risk_level(new_risk_level)
                logger.info(f"Updated risk level to {config.risk_level}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid risk level: {config.risk_level}. Must be: conservative, moderate, aggressive",
                )

        # Update monitor symbols if provided
        if config.monitor_symbols:
            # Remove old symbols
            for symbol in agent.market_monitor._monitoring_symbols.copy():
                agent.market_monitor.remove_symbol(symbol)

            # Add new symbols
            for symbol in config.monitor_symbols:
                agent.market_monitor.add_symbol(symbol)

                # Set alerts for new symbols
                threshold = config.price_alert_threshold or 5.0
                agent.market_monitor.set_percentage_threshold(symbol, threshold)

            # Update agent state config
            agent.agent_state.update_config({"monitor_symbols": config.monitor_symbols})
            logger.info(f"Updated monitor symbols to: {config.monitor_symbols}")

        # Update alert threshold if provided
        if config.price_alert_threshold:
            for symbol in agent.market_monitor._monitoring_symbols:
                agent.market_monitor.set_percentage_threshold(
                    symbol, config.price_alert_threshold
                )

            agent.agent_state.update_config(
                {"price_alert_threshold": config.price_alert_threshold}
            )
            logger.info(
                f"Updated price alert threshold to {config.price_alert_threshold}%"
            )

        # Update rebalancing interval if provided
        if config.rebalance_interval_seconds:
            agent.agent_state.update_config(
                {"rebalance_interval": config.rebalance_interval_seconds}
            )

            # Reschedule rebalancing task
            if "portfolio_rebalancing" in [
                task["id"] for task in agent.scheduler.list_tasks().values()
            ]:
                agent.scheduler.remove_task("portfolio_rebalancing")
                agent.scheduler.schedule_interval(
                    task_func=agent._run_portfolio_rebalancing,
                    interval_seconds=config.rebalance_interval_seconds,
                    task_id="portfolio_rebalancing",
                )
            logger.info(
                f"Updated rebalancing interval to {config.rebalance_interval_seconds} seconds"
            )

        # Save updated config to database
        await agent.agent_state.save_to_database()

        return SuccessResponse(
            success=True,
            message="Agent configuration updated successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update agent config: {str(e)}"
        )


@router.post("/agent/force-trade", response_model=SuccessResponse)
async def force_manual_trade(
    request: Request, trade: ManualTradeRequest
) -> SuccessResponse:
    """
    Force execute a manual trade.

    This bypasses autonomous decision making and executes a trade immediately.
    Useful for:
    - Manual intervention
    - Emergency actions
    - Testing trade execution
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        # Validate trade action
        try:
            action = trade.action.lower()
            if action not in ["buy", "sell"]:
                raise ValueError("Invalid action")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid action. Must be: buy, sell"
            )

        # Execute the forced trade
        from roma_glm.agent.agent_state import TradeAction

        success = await app_state.autonomous_agent.force_trade(
            symbol=trade.symbol,
            action=TradeAction(action),
            quantity=trade.quantity,
            price=trade.price,
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Trade execution failed (insufficient funds, no position, etc.)",
            )

        logger.info(f"Manual trade executed: {action} {trade.quantity} {trade.symbol}")
        return SuccessResponse(
            success=True,
            message=f"Manual trade executed successfully: {action} {trade.quantity} {trade.symbol}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute manual trade: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute manual trade: {str(e)}"
        )


@router.get("/agent/portfolio", response_model=dict)
async def get_portfolio_details(request: Request) -> dict:
    """
    Get detailed portfolio information.

    Returns:
    - Cash balance
    - Open positions
    - Trade history
    - Performance metrics
    - Risk metrics
    """
    app_state = get_app_state(request)

    if not app_state.autonomous_agent:
        raise HTTPException(status_code=503, detail="Autonomous Agent not available")

    try:
        portfolio = app_state.autonomous_agent.agent_state.portfolio

        # Format portfolio data for API response
        positions_data = []
        for pos in portfolio.positions:
            positions_data.append(
                {
                    "id": pos.id,
                    "symbol": pos.symbol,
                    "action": pos.action.value,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                    "created_at": pos.created_at.isoformat(),
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                }
            )

        trade_history_data = []
        for trade in portfolio.trade_history[-20:]:  # Last 20 trades
            trade_history_data.append(
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "execution_price": trade.execution_price,
                    "status": trade.status.value,
                    "reason": trade.reason,
                    "created_at": trade.created_at.isoformat(),
                    "executed_at": trade.executed_at.isoformat()
                    if trade.executed_at
                    else None,
                    "fees": trade.fees,
                }
            )

        return {
            "success": True,
            "data": {
                "portfolio": {
                    "id": portfolio.id,
                    "cash": portfolio.cash,
                    "total_value": portfolio.total_value,
                    "total_pnl": portfolio.total_pnl,
                    "total_pnl_percent": portfolio.total_pnl_percent,
                    "cash_allocation_percent": portfolio.get_cash_allocation_percent(),
                    "created_at": portfolio.created_at.isoformat(),
                    "updated_at": portfolio.updated_at.isoformat(),
                },
                "positions": positions_data,
                "trade_history": trade_history_data,
                "performance": {
                    "total_trades": len(portfolio.trade_history),
                    "positions_count": len(portfolio.positions),
                },
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get portfolio details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get portfolio details: {str(e)}"
        )
