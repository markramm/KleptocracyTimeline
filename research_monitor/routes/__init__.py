"""
Blueprint registration helper for Research Monitor API.

This module provides centralized blueprint registration for all API route modules.
Blueprints are registered in order from simple (docs, system) to complex (qa, validation_runs).
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """
    Register all route blueprints with the Flask app.

    Blueprints are registered in this specific order to ensure proper initialization
    and to make dependencies clear. Simple, stateless routes are registered first,
    followed by more complex routes with database and service dependencies.

    Args:
        app: Flask application instance

    Blueprint Registration Order:
        1. docs - API documentation (no dependencies)
        2. system - Server management and stats
        3. git - Git integration operations
        4. priorities - Research priority management
        5. timeline - Read-only timeline data access
        6. events - Event CRUD and search
        7. qa - QA validation workflow
        8. validation_runs - Validation run lifecycle
    """
    from research_monitor.routes import (
        docs,
        system,
        git,
        priorities,
        # timeline,
        # events,
        # qa,
        # validation_runs
    )

    # Register blueprints in order (uncomment as blueprints are created)
    app.register_blueprint(docs.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(git.bp)
    app.register_blueprint(priorities.bp)
    # app.register_blueprint(timeline.bp)
    # app.register_blueprint(events.bp)
    # app.register_blueprint(qa.bp)
    # app.register_blueprint(validation_runs.bp)
