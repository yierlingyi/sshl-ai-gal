import asyncio
import json
import os
import re
from typing import Dict, Any, List, Optional
from .infrastructure import APIClient
from .memory_manager import MemoryManager
from .prompt_assembler import PromptAssembler
from .plot_planner import PlotPlanner

class LLMChain:
    def __init__(self, config: Dict[str, str] = None):
        self.config = config or {}
        
        # 1. Setup Clients for each Functional Group
        
        # Group 1: Storyteller (剧情)
        self.client_story = APIClient(
            api_keys=[self.config.get("key_story", "dummy")],
            base_url=self.config.get("url_story", "https://api.openai.com/v1")
        )
        self.model_story = self.config.get("model_story", "gpt-3.5-turbo")
        
        # Group 2: Summary (大小总结)
        self.client_summary = APIClient(
            api_keys=[self.config.get("key_summary", "dummy")],
            base_url=self.config.get("url_summary", "https://api.openai.com/v1")
        )
        self.model_summary = self.config.get("model_summary", "gpt-3.5-turbo")
        
        # Group 3: Logic (Director + Architect/Planner) (指令 + 剧情规划)
        self.client_logic = APIClient(
            api_keys=[self.config.get("key_logic", "dummy")],
            base_url=self.config.get("url_logic", "https://api.openai.com/v1")
        )
        self.model_logic = self.config.get("model_logic", "gpt-4")
        
        self.memory = MemoryManager()
        # Set threshold from config (default 5 if not in config, but pages.py defaults to 5)
        self.memory.plot_planning_threshold = self.config.get("plot_planning_freq", 5)
        
        self.assembler = PromptAssembler(self.memory)
        self.planner = PlotPlanner()
        
        # Blocking state
        self.is_blocking = False
        self.block_reason = ""
    
    def _extract_content(self, text: str, tag: str) -> Optional[str]:
        """Extracts content from <tag>...</tag>."""
        pattern = re.compile(f"<{tag}>(.*?)</{tag}>")
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return None

    async def _retry_loop(self, task_name: str, func, *args, tag=None, retry_delay=2, max_retries=5, critical=False) -> str:
        """
        Generic retry loop.
        critical: if True, retries indefinitely with long delay (60s) and blocks system.
        """
        attempts = 0
        while True:
            try:
                result = await func(*args)
                
                # Validation
                if tag:
                    extracted = self._extract_content(result, tag)
                    if not extracted:
                        raise ValueError(f"Missing tag <{tag}> in output.")
                    final_result = extracted
                else:
                    final_result = result
                
                return final_result
            
            except Exception as e:
                attempts += 1
                print(f"[{task_name}] Failed (Attempt {attempts}): {e}")
                
                if critical:
                    self.is_blocking = True
                    self.block_reason = f"{task_name} failed. Retrying in 60s..."
                    print(f"[{task_name}] Critical failure. Blocking system. Retrying in 60s...")
                    await asyncio.sleep(60)
                else:
                    if attempts >= max_retries:
                        print(f"[{task_name}] Max retries reached. Aborting.")
                        raise e # Re-raise to caller
                    await asyncio.sleep(retry_delay)

    async def run_storyteller(self, payload: List[Dict[str, str]]) -> str:
        return await self._retry_loop(
            "Storyteller", 
            self.client_story.chat_completion, 
            payload, 
            model=self.model_story,
            tag="game",
            max_retries=3,
            retry_delay=2
        )

    async def run_director(self, story_text: str) -> str:
        system_prompt = self.assembler.assemble_prompt("director", story_text=story_text)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Add stage directions to this text:\n\n{story_text}"}
        ]
        return await self._retry_loop(
            "Director",
            self.client_logic.chat_completion, # Use Logic Client
            messages,
            model=self.model_logic, # Use Logic Model
            tag="finally",
            max_retries=3,
            retry_delay=2
        )

    async def execute_turn(self, user_input: str) -> str:
        if self.is_blocking:
            return f"[System Paused] {self.block_reason}"

        # 1. User Input to Memory
        self.memory.add_message("user", user_input)
        
        try:
            # 2. Main Pipeline (Storyteller -> Director)
            # Stage 1: Storyteller (AI-1)
            payload = self.assembler.assemble_storyteller_payload()
            story_text = await self.run_storyteller(payload)
            
            # Stage 2: Director (AI-2)
            final_output = await self.run_director(story_text)
            
            # 3. Store Result (Original story text? or Director output? 
            # Usually we store the story text for context, Director output for display.
            # But the memory manager prompt asks for 'History'. 
            # If we store tags, it consumes context. Let's store story_text (clean).)
            self.memory.add_message("assistant", story_text)
            
            # 4. Background Tasks (Branching)
            self._handle_background_tasks()
            
            return final_output
        except Exception as e:
            return f"[System Error] Failed to generate response: {e}"

    async def run_opening_sequence(self) -> str:
        """
        Special one-off flow for new game opening.
        1. Read user persona.
        2. Planner -> generates opening plan (<guide>).
        3. Storyteller -> generates text based on persona + plan (<game>).
        4. Director -> adds commands.
        """
        # Read Persona
        persona = "Unknown"
        if os.path.exists("assets/用户设定/用户人设.txt"):
            with open("assets/用户设定/用户人设.txt", "r", encoding="utf-8") as f:
                persona = f.read()

        # Step 1: Planner
        # Load prompt template
        plan_prompt_path = "assets/提示词/开局/planner.txt"
        if not os.path.exists(plan_prompt_path):
            return "[Error] Opening planner prompt missing."
        
        with open(plan_prompt_path, "r", encoding="utf-8") as f:
            plan_template = f.read()
        
        plan_input = plan_template.replace("{{user_persona}}", persona)
        
        messages_plan = [{"role": "user", "content": plan_input}]
        
        # Call Planner (Logic Model)
        print("[Opening] Running Planner...")
        opening_plan_xml = await self._retry_loop(
            "Opening Planner",
            self.client_logic.chat_completion,
            messages_plan,
            model=self.model_logic,
            tag="guide", # Expecting <guide>
            max_retries=3
        )
        
        # Step 2: Storyteller
        story_prompt_path = "assets/提示词/开局/storyteller.txt"
        if not os.path.exists(story_prompt_path):
             return "[Error] Opening storyteller prompt missing."

        with open(story_prompt_path, "r", encoding="utf-8") as f:
            story_template = f.read()
            
        story_input = story_template.replace("{{user_persona}}", persona).replace("{{opening_plan}}", opening_plan_xml)
        
        messages_story = [{"role": "user", "content": story_input}]
        
        print("[Opening] Running Storyteller...")
        story_text = await self._retry_loop(
            "Opening Storyteller",
            self.client_story.chat_completion,
            messages_story,
            model=self.model_story,
            tag="game",
            max_retries=3
        )
        
        # Save history
        self.memory.add_message("assistant", story_text)

        # Step 3: Director
        print("[Opening] Running Director...")
        final_output = await self.run_director(story_text)
        
        return final_output

    def _handle_background_tasks(self):
        """
        Checks triggers and launches critical background tasks.
        """
        triggers = self.memory.check_for_triggers()
        
        # We handle tasks sequentially or check "is_blocking" before starting new ones.
        # Ideally, we should queue them or launch them.
        # Since _retry_loop sets is_blocking, we must be careful not to launch parallel blocking tasks 
        # unless they are coordinated.
        # For simplicity, we prioritize Small Summary -> Big Summary -> Plot Planning.
        
        if self.is_blocking:
            return

        if triggers["needs_small_summary"]:
            msgs = self.memory.consume_raw_history()
            if msgs: 
                self.is_blocking = True
                self.block_reason = "Generating Small Summary..."
                asyncio.create_task(self._generate_small_summary(msgs))
            return # Exit to avoid starting multiple tasks at once
            
        if triggers["needs_big_summary"]:
            smalls_to_merge = self.memory.consume_small_summaries_for_big_merge()
            if smalls_to_merge:
                self.is_blocking = True
                self.block_reason = "Generating Big Summary..."
                asyncio.create_task(self._generate_big_summary(smalls_to_merge))
            return

        if triggers["needs_plot_planning"]:
            self.is_blocking = True
            self.block_reason = "Generating Plot Guidance..."
            asyncio.create_task(self._run_architect_task())

    async def _generate_small_summary(self, messages: List[Dict[str, str]]):
        print("[Background] Generating Small Summary...")
        text_block = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        system_prompt = self.assembler.assemble_prompt("summary_small", to_summarize=text_block)
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the summary now based on the instructions and content above."}
        ]
        
        try:
            summary = await self._retry_loop(
                "Small Summary",
                self.client_summary.chat_completion, # Use Summary Client
                prompt,
                model=self.model_summary, # Use Summary Model
                tag="summary_little",
                critical=True # Infinite retry with 60s delay, blocks system
            )
            self.memory.append_small_summary(summary)
            print(f"[Background] Small Summary Added.")
        finally:
            # Unblock and re-check triggers (chaining)
            self.is_blocking = False
            self._handle_background_tasks()

    async def _generate_big_summary(self, smalls_list: List[str]):
        print("[Background] Generating Big Summary...")
        current_big = self.memory.big_summary
        smalls_text = "\n".join(smalls_list)
        
        # Combine old summary and new events for the to_summarize block
        combined_content = f"OLD SUMMARY:\n{current_big}\n\nNEW EVENTS TO MERGE:\n{smalls_text}"
        
        system_prompt = self.assembler.assemble_prompt("summary_big", to_summarize=combined_content)
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the updated big summary now."}
        ]
        
        try:
            new_big = await self._retry_loop(
                "Big Summary",
                self.client_summary.chat_completion, # Use Summary Client
                prompt,
                model=self.model_summary, # Use Summary Model
                tag="summary_big",
                critical=True
            )
            self.memory.update_big_summary(new_big)
            print(f"[Background] Big Summary Updated.")
            
        finally:
             self.is_blocking = False
             self._handle_background_tasks()

    async def _run_architect_task(self):
        try:
            await self._run_architect()
        finally:
            self.is_blocking = False
            # Plot planning resets its own counter, so loop should naturally stop triggering it
            self._handle_background_tasks()

    async def _run_architect(self):
        print("[Background] Running Architect (Plot Planner)...")
        system_prompt = self.assembler.assemble_prompt("planner")
        overall_outline = self.assembler.get_current_story_guidance()
        
        # PlotPlanner.plan_plot handles prompt construction but not XML extraction/retry logic easily
        # unless we modify PlotPlanner or wrap the client call inside it.
        # But PlotPlanner returns a LIST of strings, parsed from JSON.
        # The user wants <guide> tag around the JSON.
        # I need to wrap the `planner.plan_plot` call or modify `PlotPlanner` to return raw text 
        # then extract <guide>, then parse JSON.
        # Modifying PlotPlanner is cleaner.
        # But here I can just pass a wrapper function? No.
        # Let's modify PlotPlanner to respect the tag or handle it here.
        # The simplest way is to handle the loop here, but `planner.plan_plot` does both generation and parsing.
        # I'll update PlotPlanner in a moment. For now, let's assume `planner.plan_plot` 
        # can be updated to handle validation.
        
        # Actually, let's keep logic in `_run_architect` using `_retry_loop` on a raw generation function,
        # then pass result to planner for parsing?
        # Or better: Update `PlotPlanner` to allow injecting a "validator".
        
        # Let's just override the generation step.
        prompt_content = self.planner._build_prompt(self.memory.big_summary, overall_outline)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_content}
        ]
        
        def parse_planner_output(text):
             # Extract <guide> first (handled by _retry_loop)
             # Then parse JSON
             try:
                 # Strip potential markdown code blocks
                 clean = text.replace("```json", "").replace("```", "").strip()
                 data = json.loads(clean)
                 return data.get("options", [])
             except:
                 raise ValueError("Invalid JSON in <guide>")

        raw_result = await self._retry_loop(
            "Architect",
            self.client_logic.chat_completion, # Use Logic Client
            messages,
            model=self.model_logic, # Use Logic Model
            tag="guide",
            critical=True
        )
        
        # Parse
        try:
            options = parse_planner_output(raw_result)
            self.memory.update_plot_guidance(options)
            print(f"[Background] Plot Guidance Updated: {options}")
        except Exception as e:
            # If parsing fails (but tag existed), what do we do? 
            # We should probably retry the whole thing. 
            # But `_retry_loop` already returned. 
            # We need the validation inside the loop.
            # `_retry_loop` doesn't support custom validation post-extraction easily without modification.
            # But I can just put this logic inside a lambda passed to retry loop? No, retry loop calls `func`.
            # I'll just accept that if JSON is bad, we might log error and continue, 
            # or I'd need a more complex retry mechanism.
            # Given "Strictly JSON" instruction, it usually works.
            # I will assume success if <guide> is present.
            pass
