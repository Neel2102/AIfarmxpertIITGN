from __future__ import annotations
from typing import Dict, Any, List
from farmxpert.core.base_agent.base_agent import BaseAgent


class LogisticsStorageAgent(BaseAgent):
    name = "logistics_storage_agent"
    description = "Helps plan post-harvest activities: when to store, sell, or transport based on price windows and spoilage risks"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide logistics and storage recommendations"""
        crops = inputs.get("crops", [])
        harvest_quantity = inputs.get("harvest_quantity", {})
        storage_capacity = inputs.get("storage_capacity", 0)
        
        # Generate storage recommendations
        storage_recommendations = self._generate_storage_recommendations(crops, harvest_quantity, storage_capacity)
        
        # Plan logistics
        logistics_plan = self._plan_logistics(crops, harvest_quantity)
        
        return {
            "agent": self.name,
            "crops": crops,
            "storage_recommendations": storage_recommendations,
            "logistics_plan": logistics_plan,
            "recommendations": self._generate_recommendations(crops, storage_capacity)
        }
    
    def _generate_storage_recommendations(self, crops: List[str], harvest_quantity: Dict, storage_capacity: float) -> Dict[str, Any]:
        """Generate storage recommendations for crops"""
        recommendations = {
            "immediate_sale": [],
            "short_term_storage": [],
            "long_term_storage": [],
            "storage_requirements": {}
        }
        
        for crop in crops:
            quantity = harvest_quantity.get(crop, 0)
            
            # Determine storage strategy based on crop characteristics
            if crop in ["sugarcane", "vegetables"]:
                recommendations["immediate_sale"].append({
                    "crop": crop,
                    "quantity": quantity,
                    "reason": "Perishable crop - sell immediately"
                })
            elif crop in ["wheat", "maize", "rice"]:
                if storage_capacity >= quantity * 0.5:
                    recommendations["long_term_storage"].append({
                        "crop": crop,
                        "quantity": quantity * 0.5,
                        "reason": "Stable crop - can be stored for better prices"
                    })
                    recommendations["immediate_sale"].append({
                        "crop": crop,
                        "quantity": quantity * 0.5,
                        "reason": "Sell portion for immediate cash flow"
                    })
                else:
                    recommendations["immediate_sale"].append({
                        "crop": crop,
                        "quantity": quantity,
                        "reason": "Insufficient storage capacity"
                    })
            else:
                recommendations["short_term_storage"].append({
                    "crop": crop,
                    "quantity": quantity,
                    "reason": "Moderate storage life"
                })
        
        return recommendations
    
    def _plan_logistics(self, crops: List[str], harvest_quantity: Dict) -> Dict[str, Any]:
        """Plan logistics for crop transportation"""
        logistics = {
            "transport_requirements": {},
            "timeline": {},
            "cost_estimates": {}
        }
        
        for crop in crops:
            quantity = harvest_quantity.get(crop, 0)
            
            logistics["transport_requirements"][crop] = {
                "quantity_tons": quantity,
                "vehicle_type": "truck" if quantity < 10 else "truck_combination",
                "trips_needed": max(1, int(quantity / 5))  # 5 tons per trip
            }
            
            logistics["cost_estimates"][crop] = {
                "transport_cost": quantity * 100,  # 100 per ton
                "loading_cost": quantity * 20,
                "total_cost": quantity * 120
            }
        
        return logistics
    
    def _generate_recommendations(self, crops: List[str], storage_capacity: float) -> List[str]:
        """Generate logistics recommendations"""
        return [
            "Prioritize immediate sale of perishable crops",
            "Store stable crops for better market prices",
            "Plan transportation during off-peak hours",
            "Ensure proper packaging for long-distance transport",
            "Consider cold storage for temperature-sensitive crops"
        ]
