import json
from typing import List, Dict, Any
from .infrastructure import APIClient

class PlotPlanner:
    """
    AI-3: The Architect.
    Predicts and plans the future plot direction.
    """
    
    SYSTEM_PROMPT = """You are the Lead Writer (Architect) for a visual novel. 
Your goal is to analyze the current story state and propose 3 distinct, interesting plot developments.
Output STRICTLY in JSON format with a key 'options' containing a list of 3 strings.
"""

    def _build_prompt(self, big_summary: str, overall_outline: str) -> str:
        # User requested strictly: Plot Planning Prompt + Big Summary
        # And "Add this Overall Outline ... empty if empty".
        
        outline_section = ""
        if overall_outline:
            outline_section = f"\n# Overall Story Outline (Guidance)\n{overall_outline}\n"
        
        return f"""
Analyze the following story context:

# Global Story Summary
{big_summary}
{outline_section}
Based on this, generate 3 distinct potential plot directions for the next segment.
1. Logical/Expected progression.
2. A surprising twist or conflict.
3. A character-focused emotional development.

Respond in JSON: {{ "options": ["direction 1...", "direction 2...", "direction 3..."] }}
"""

    async def plan_plot(self, client: APIClient, big_summary: str, small_summaries: List[str], overall_outline: str = "", model: str = "gpt-4", system_prompt: str = None) -> List[str]:
        prompt = self._build_prompt(big_summary, overall_outline)
        
        sys_prompt = system_prompt if system_prompt else self.SYSTEM_PROMPT
        
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await client.chat_completion(messages, model=model)
        
        try:
            # Simple parsing, in production use a robust JSON parser or Pydantic
            # Strip markdown code blocks if present
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            return data.get("options", [])
        except json.JSONDecodeError:
            print(f"[PlotPlanner] Failed to parse JSON: {response_text}")
            return ["Continue the story naturally."]
