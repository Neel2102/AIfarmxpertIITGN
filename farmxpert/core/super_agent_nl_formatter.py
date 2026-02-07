"""
Natural Language Formatter for SuperAgent Responses
Converts structured JSON responses into clean, conversational natural language
"""

from typing import Dict, Any, List


def format_response_as_natural_language(
    query: str,
    response_data: Dict[str, Any],
    agent_names: List[str],
    context: Dict[str, Any] = None
) -> str:
    """
    Convert structured response into natural language
    
    Args:
        query: Original user query
        response_data: Structured response from agents
        agent_names: List of agents that contributed
        context: Optional context (locale, conversational mode, etc.)
        
    Returns:
        Clean natural language response string
    """
    # Check if conversational mode is enabled
    conversational = context.get("conversational", False) if context else False
    
    # Extract key components
    answer = response_data.get("answer", "")
    recommendations = response_data.get("recommendations", [])
    warnings = response_data.get("warnings", [])
    next_steps = response_data.get("next_steps", [])
    
    # Build natural language response
    parts = []
    
    # Main answer
    if answer:
        parts.append(answer)
    
    # Recommendations
    if recommendations:
        if conversational:
            parts.append("\n\nHere's what I recommend:")
        else:
            parts.append("\n\n**Recommendations:**")
        for i, rec in enumerate(recommendations, 1):
            parts.append(f"\n{i}. {rec}")
    
    # Warnings
    if warnings:
        if conversational:
            parts.append("\n\n⚠️ Important things to note:")
        else:
            parts.append("\n\n**Important Warnings:**")
        for warning in warnings:
            parts.append(f"\n• {warning}")
    
    # Next steps
    if next_steps:
        if conversational:
            parts.append("\n\nNext, you should:")
        else:
            parts.append("\n\n**Next Steps:**")
        for i, step in enumerate(next_steps, 1):
            parts.append(f"\n{i}. {step}")
    
    # Fallback if no content
    if not parts:
        return "I understand your question, but I need more information to provide a helpful answer. Could you please provide more details about your crop, location, or specific concern?"
    
    return "".join(parts)


def create_simple_greeting_response(query: str) -> str:
    """Handle simple greetings intelligently"""
    q_lower = query.lower().strip()
    
    # Greetings
    if q_lower in ["hi", "hello", "hey", "namaste", "namaskar"]:
        return ("Hello! I'm FarmXpert, your AI farming assistant. "
                "I can help you with crop selection, pest management, irrigation planning, "
                "weather forecasts, and much more. What would you like to know about your farm today?")
    
    # How are you
    if any(phrase in q_lower for phrase in ["how are you", "how r u", "what's up", "whats up"]):
        return ("I'm doing great, thank you for asking! I'm here and ready to help you with "
                "all your farming needs. What can I assist you with today?")
    
    # Thank you
    if any(phrase in q_lower for phrase in ["thank you", "thanks", "thank u", "dhanyavaad"]):
        return ("You're very welcome! I'm always here to help. Feel free to ask me anything "
                "about farming, crops, weather, or agricultural best practices anytime!")
    
    # Goodbye
    if any(phrase in q_lower for phrase in ["bye", "goodbye", "see you", "good night"]):
        return ("Goodbye! Wishing you a bountiful harvest. Come back anytime you need farming advice. "
                "Happy farming! 🌾")
    
    return None  # Not a simple greeting


def is_simple_query(query: str) -> bool:
    """Check if query is a simple greeting/small talk"""
    q_lower = query.lower().strip()
    simple_patterns = [
        "hi", "hello", "hey", "namaste", "namaskar",
        "how are you", "how r u", "what's up", "whats up",
        "thank you", "thanks", "thank u", "dhanyavaad",
        "bye", "goodbye", "see you", "good night"
    ]
    return any(pattern in q_lower for pattern in simple_patterns)
