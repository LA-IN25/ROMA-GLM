"""Solver setup that adapts ROMA configs for prompt optimization."""

from typing import Optional

from roma_glm import RecursiveSolverModule
from roma_glm.config import load_config
from roma_glm.core.engine.solve import RecursiveSolver

from .config import OptimizationConfig, patch_romaconfig


def create_solver_module(
    config: OptimizationConfig,
    *,
    profile: Optional[str] = None
) -> RecursiveSolverModule:
    """
    Create a RecursiveSolverModule configured with optimization-specific settings.

    Args:
        config: Prompt optimization configuration.
        profile: Optional ROMA config profile to load before patching.

    Returns:
        RecursiveSolverModule wired to a RecursiveSolver that uses optimization LMs.
    """
    base_config = load_config(profile=profile)
    patched_config = patch_romaconfig(config, base_config)

    solver = RecursiveSolver(
        config=patched_config,
        max_depth=config.max_depth,
        enable_logging=config.enable_logging,
        enable_checkpoints=False,
    )
    return RecursiveSolverModule(solver=solver)
