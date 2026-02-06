from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import asyncio
import time
from farmxpert.core.base_agent.agent_registry import list_agents, create_agent


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def get_agents() -> Dict[str, str]:
    return list_agents()


@router.post("/smoke-test")
async def smoke_test_agents(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body = body or {}
    requested_agents = body.get("agents")
    timeout_s = float(body.get("timeout_s") or 25)

    all_agents = list(list_agents().keys())
    agents: List[str] = all_agents
    if isinstance(requested_agents, list) and requested_agents:
        agents = [a for a in requested_agents if isinstance(a, str)]

    common_context = {
        "location": {"state": "Gujarat", "district": "Surat", "latitude": 21.1702, "longitude": 72.8311},
        "season": "Kharif",
        "land_size_acre": 3,
        "risk_preference": "Low",
        "farm_location": "Surat, Gujarat",
        "farm_size": "3 acres",
        "current_season": "Rainy",
    }

    def _payload_for(agent_name: str) -> Dict[str, Any]:
        if agent_name == "crop_selector":
            return {"query": "What crops should I plant this season?", "context": common_context}
        if agent_name == "seed_selection":
            return {"query": "Which seed variety is best for cotton?", "context": {**common_context, "crop": "cotton"}}
        if agent_name == "soil_health":
            return {
                "query": "Analyze my soil health",
                "context": {
                    **common_context,
                    "soil_data": {
                        "pH": 7.1,
                        "nitrogen": 45,
                        "phosphorus": 18,
                        "potassium": 110,
                        "electrical_conductivity": 1.2,
                        "moisture": 32,
                        "temperature": 26,
                    },
                },
            }
        if agent_name == "fertilizer_advisor":
            return {
                "query": "Suggest fertilizer schedule",
                "context": {**common_context, "soil_data": {"pH": 7.1, "N": 45, "P": 18, "K": 110}, "crop": "cotton"},
            }
        if agent_name == "irrigation_planner":
            return {
                "query": "Plan irrigation schedule",
                "context": {**common_context, "crop": "cotton", "soil_type": "loamy", "weather": {"temperature": 30, "humidity": 70}},
            }
        if agent_name == "weather_watcher":
            return {"query": "Weather forecast for next 7 days", "context": {**common_context, "farm_location": "Surat, Gujarat"}}
        if agent_name == "growth_monitor":
            return {"query": "What should I do at 25 days after sowing?", "context": {**common_context, "crop": "cotton", "days_after_sowing": 25}}
        if agent_name == "market_intelligence":
            return {"query": "Current cotton price trend", "context": {**common_context, "crop": "cotton", "market": "Surat"}}
        if agent_name == "task_scheduler":
            return {"query": "Schedule farm tasks this week", "context": {**common_context, "crop": "cotton", "tasks": ["weeding", "irrigation", "spraying"]}}
        if agent_name == "pest_diagnostic":
            return {"query": "Leaves have spots and curling", "context": {**common_context, "crop": "cotton", "symptoms": "spots and curling"}}

        if agent_name == "yield_predictor":
            return {
                "query": "Predict yield",
                "context": {
                    **common_context,
                    "yield_request": {
                        "State_Name": "Gujarat",
                        "District_Name": "Surat",
                        "Crop": "Cotton",
                        "Season": "Kharif",
                        "Crop_Year": 2024,
                        "Area": 1.0,
                    },
                },
            }

        if agent_name == "profit_optimization":
            return {
                "query": "Optimize profit",
                "context": {
                    **common_context,
                    "crop": "cotton",
                    "area_acre": 3,
                    "yield_per_acre": 8,
                    "expenses": [
                        {"name": "seed", "amount": 1500},
                        {"name": "fertilizer", "amount": 2200},
                        {"name": "labor", "amount": 3000},
                    ],
                    "market_prices": {"Surat": 6200, "Bharuch": 6050},
                },
            }

        return {"query": "Smoke test", "context": common_context}

    async def _run_one(a: str) -> Dict[str, Any]:
        start = time.time()
        try:
            agent = create_agent(a)
        except KeyError:
            return {"agent": a, "ok": False, "error": "Unknown agent"}

        payload = _payload_for(a)
        try:
            res = await asyncio.wait_for(agent.handle(payload), timeout=timeout_s)
            if isinstance(res, dict):
                has_error_flag = bool(res.get("error")) and res.get("success") is not True
                ok = bool(res.get("success", True)) and not has_error_flag
                response = res.get("response")
                if response is None and res.get("message"):
                    response = res.get("message")
                if response is None and res.get("error"):
                    response = str(res.get("error"))
            else:
                ok = True
                response = None
            return {
                "agent": a,
                "ok": ok,
                "elapsed_s": round(time.time() - start, 3),
                "response": (response[:160] if isinstance(response, str) else response),
            }
        except Exception as e:
            return {"agent": a, "ok": False, "elapsed_s": round(time.time() - start, 3), "error": str(e)[:300]}

    results = await asyncio.gather(*[_run_one(a) for a in agents])
    bad = [r["agent"] for r in results if not r.get("ok")]
    return {
        "ok": len(bad) == 0,
        "total": len(results),
        "bad": bad,
        "results": results,
    }


@router.post("/{agent_name}")
async def invoke_agent(agent_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        agent = create_agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")
    return await agent.handle(inputs)


