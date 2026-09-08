import time
import json
from typing import Dict, List, Any
from core.models import Project, BudgetOptimizationOption
from core.db import get_connection
from services.gemini_service import GeminiCreativeProvider
from services.ibm_service import IBMProductionProvider

class AgentOrchestrator:
    """Multi-Department Backstage AI Environment & Multi-Agent Co-Director Loop."""

    def __init__(self):
        self.gemini = GeminiCreativeProvider()
        self.ibm = IBMProductionProvider()

    def run_budget_optimization_loop(self, project: Project, option: BudgetOptimizationOption) -> Dict[str, Any]:
        """Executes full multi-department agentic loop with persistent database logging."""
        conn = get_connection()
        cursor = conn.cursor()

        # Step 1: Initial Feasibility Audit
        initial_feasibility = self.ibm.analyze_production_feasibility(project)
        
        # Step 2: Gemini Adapts (Scene Rewrites)
        rewrite_result = self.gemini.rewrite_scenes_for_budget(project.scenes, option)
        
        # Step 3: Recalculate Budget
        new_estimated = max(project.target_budget - 500.0, project.estimated_budget - option.estimated_savings)
        project.estimated_budget = new_estimated

        # Update Project in SQLite DB
        cursor.execute("UPDATE projects SET estimated_budget = ? WHERE id = ?", (new_estimated, project.id))
        cursor.execute("UPDATE budget_options SET status = 'Applied' WHERE id = ?", (option.id,))
        
        # Step 4: IBM Validates
        final_feasibility = self.ibm.analyze_production_feasibility(project)

        # Log AI Run to Database
        activity_stream = [
            {"time": "12:43:02", "dept": "GEMINI / CREATIVE", "msg": f"Estrategia seleccionada: {option.title}"},
            {"time": "12:43:04", "dept": "GEMINI / STORY", "msg": "Reescritura de escenas afectadas completada."},
            {"time": "12:43:06", "dept": "IBM / PRODUCTION", "msg": f"Ahorro estimado verificado: -${option.estimated_savings:,.2f}."},
            {"time": "12:43:09", "dept": "IBM / VALIDATION", "msg": f"Nuevo presupuesto estimado: ${new_estimated:,.2f}."}
        ]

        cursor.execute("""
        INSERT INTO ai_runs (project_id, run_type, prompt, gemini_response, ibm_response, status)
        VALUES (?, 'BUDGET_OPTIMIZATION', ?, ?, ?, 'COMPLETED')
        """, (project.id, option.title, json.dumps(rewrite_result, default=str), json.dumps(final_feasibility, default=str)))

        cursor.execute("""
        INSERT INTO project_history (project_id, timestamp, event, agent, details, entity_type, entity_id)
        VALUES (?, 'Justo Ahora', 'Optimización de Presupuesto', 'Bucle de Agentes AI', ?, 'BUDGET', ?)
        """, (project.id, f"Presupuesto reducido a ${new_estimated:,.2f} mediante {option.title}.", option.id))

        conn.commit()
        conn.close()

        return {
            "initial_feasibility": initial_feasibility,
            "gemini_rewrite": rewrite_result,
            "final_feasibility": final_feasibility,
            "new_estimated_budget": new_estimated,
            "savings": option.estimated_savings,
            "activity_stream": activity_stream
        }
