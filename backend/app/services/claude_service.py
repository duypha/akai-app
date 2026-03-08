"""
Claude Service - Handles AI Vision and Chat using Anthropic Claude
"""

import os
import anthropic
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"  # Use Claude Sonnet for good balance of speed/quality
        self.vision_model = "claude-sonnet-4-20250514"  # Vision capable model

        # System prompt - Friendly AI assistant with screen vision and UI skills
        self.system_prompt = """You're a friendly AI buddy who can see the user's screen.

YOUR SKILLS:
1. General help - answer questions, chat, assist with tasks
2. Tech support - troubleshoot issues, guide fixes
3. UI/UX Design - analyze interfaces, suggest improvements
4. Code review - read and comment on code

UI/UX ANALYSIS (when asked or when reviewing designs):
- Layout: spacing, alignment, visual hierarchy
- Colors: contrast, harmony, accessibility
- Typography: readability, font pairing, sizing
- UX: user flow, clarity, call-to-actions
- Consistency: patterns, components, style
- Accessibility: color contrast, text size, touch targets
- Suggestions: specific actionable improvements

HOW TO RESPOND:
- Short sentences, one idea each
- Put each thought on its own line (blank line between)
- No special characters, no bullets, no asterisks
- Just plain simple text
- Max 3-5 lines total (more if doing detailed UI review)

VIBE:
- Text like a friend
- Casual and warm
- No filler words
- Skip the formalities

UI REVIEW EXAMPLE:
Nice clean layout.

The button needs more contrast though.

Try making it darker blue on that light background.

Also bump up the font size on mobile.

TECH HELP EXAMPLE:
WiFi's disconnected.

Click the network icon bottom right.

Pick your network.

You'll be back online in a sec."""

    async def analyze_screen(
        self,
        image_base64: str,
        user_message: Optional[str] = None,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze a screenshot using Claude Vision

        Args:
            image_base64: Base64 encoded screenshot image
            user_message: User's question or description of the problem
            conversation_history: Previous messages in the conversation

        Returns:
            Dict with 'response' key containing AI's analysis
        """
        try:
            # Build messages array
            messages = []

            # Add conversation history (excluding images for token efficiency)
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Build current message with image
            content = []

            # Add the screenshot
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            })

            # Add user's message or default prompt
            if user_message:
                content.append({
                    "type": "text",
                    "text": user_message
                })
            else:
                content.append({
                    "type": "text",
                    "text": "What do you see on this screen? Describe what's happening and share any relevant observations or insights."
                })

            messages.append({
                "role": "user",
                "content": content
            })

            # Call Claude API
            response = self.client.messages.create(
                model=self.vision_model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages
            )

            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble analyzing the screen right now. Please try again in a moment.",
                "error": str(e)
            }

    async def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Chat with Claude without an image

        Args:
            message: User's message
            conversation_history: Previous messages in the conversation

        Returns:
            Dict with 'response' key containing AI's response
        """
        try:
            # Build messages array
            messages = []

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages
            )

            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble responding right now. Please try again in a moment.",
                "error": str(e)
            }

    async def plan_task(
        self,
        goal: str,
        current_screen: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Plan a series of steps to accomplish a goal

        Args:
            goal: What the user wants to achieve
            current_screen: Base64 encoded screenshot of current state
            conversation_history: Previous messages

        Returns:
            Dict with planned steps
        """
        planning_prompt = f"""The user wants to: {goal}

Please analyze the current screen and create a step-by-step plan to help them achieve this goal.

For each step, specify:
1. What action to take (click, type, scroll, etc.)
2. What element to interact with (describe it clearly)
3. What should happen after the action
4. How to verify the step was successful

Format your response as a numbered list of clear, specific steps."""

        return await self.analyze_screen(
            image_base64=current_screen,
            user_message=planning_prompt,
            conversation_history=conversation_history
        )

    def _format_kb_context(self, kb_context: Dict[str, Any]) -> str:
        """
        Format Knowledge Base context for the system prompt

        Args:
            kb_context: KB search results with problems and solutions

        Returns:
            Formatted string for system prompt
        """
        if not kb_context or not kb_context.get("has_matches"):
            return ""

        lines = ["\n--- KNOWLEDGE BASE MATCHES ---"]

        problems = kb_context.get("problems", [])
        for i, problem in enumerate(problems[:3], 1):
            lines.append(f"\nProblem {i}: {problem['title']} (Category: {problem['category']})")
            lines.append(f"Description: {problem['description']}")

            solutions = problem.get("solutions", [])
            for j, solution in enumerate(solutions[:2], 1):
                success_rate = solution.get("success_rate", 0)
                lines.append(f"  Solution {j}: {solution['title']} (Success rate: {success_rate:.0%})")
                lines.append(f"    ID: {solution['id']}")
                lines.append("    Steps:")
                for step in solution.get("steps", []):
                    lines.append(f"      - {step}")

        lines.append("\n--- END KB MATCHES ---")
        return "\n".join(lines)

    def _format_task_context(self, task_context: Dict[str, Any]) -> str:
        """
        Format Task Plan context for the system prompt

        Args:
            task_context: Active task plan data

        Returns:
            Formatted string for system prompt
        """
        if not task_context or not task_context.get("has_active_plan"):
            return ""

        plan = task_context.get("plan", {})
        current_step = task_context.get("current_step")
        progress = task_context.get("progress", {})

        lines = ["\n--- ACTIVE TASK PLAN ---"]
        lines.append(f"Plan: {plan.get('title', 'Unknown')}")
        lines.append(f"Progress: {progress.get('completed', 0)}/{progress.get('total', 0)} steps completed ({progress.get('percent', 0)}%)")

        if current_step:
            lines.append(f"\nCURRENT STEP ({current_step.get('order', '?')}/{progress.get('total', '?')}):")
            lines.append(f"  Title: {current_step.get('title', 'Unknown')}")
            lines.append(f"  Description: {current_step.get('description', 'No description')}")
            lines.append(f"  Step ID: {current_step.get('id', '')}")
            lines.append("\nGuide the user through this step. When they complete it, they can mark it done.")
        else:
            lines.append("\nAll steps have been addressed.")

        lines.append("\n--- END TASK PLAN ---")
        return "\n".join(lines)

    async def chat_with_context(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        kb_context: Dict[str, Any] = None,
        task_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Chat with Claude including KB and task context

        Args:
            message: User's message
            conversation_history: Previous messages
            kb_context: Knowledge Base search results
            task_context: Active task plan data

        Returns:
            Dict with 'response' key containing AI's response
        """
        try:
            # Build enhanced system prompt
            enhanced_prompt = self.system_prompt

            # Add KB context
            kb_section = self._format_kb_context(kb_context)
            if kb_section:
                enhanced_prompt += kb_section

            # Add task context
            task_section = self._format_task_context(task_context)
            if task_section:
                enhanced_prompt += task_section

            # Build messages array
            messages = []

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=enhanced_prompt,
                messages=messages
            )

            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "had_kb_context": bool(kb_section),
                "had_task_context": bool(task_section)
            }

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble responding right now. Please try again in a moment.",
                "error": str(e)
            }

    async def analyze_screen_with_context(
        self,
        image_base64: str,
        user_message: Optional[str] = None,
        conversation_history: List[Dict] = None,
        kb_context: Dict[str, Any] = None,
        task_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze a screenshot with KB and task context

        Args:
            image_base64: Base64 encoded screenshot
            user_message: User's question
            conversation_history: Previous messages
            kb_context: Knowledge Base search results
            task_context: Active task plan data

        Returns:
            Dict with 'response' key containing AI's analysis
        """
        try:
            # Build enhanced system prompt
            enhanced_prompt = self.system_prompt

            # Add KB context
            kb_section = self._format_kb_context(kb_context)
            if kb_section:
                enhanced_prompt += kb_section

            # Add task context
            task_section = self._format_task_context(task_context)
            if task_section:
                enhanced_prompt += task_section

            # Build messages array
            messages = []

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Build current message with image
            content = []
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            })

            if user_message:
                content.append({
                    "type": "text",
                    "text": user_message
                })
            else:
                content.append({
                    "type": "text",
                    "text": "What do you see on this screen? Describe what's happening and share any relevant observations or insights."
                })

            messages.append({
                "role": "user",
                "content": content
            })

            # Call Claude API
            response = self.client.messages.create(
                model=self.vision_model,
                max_tokens=2048,
                system=enhanced_prompt,
                messages=messages
            )

            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "had_kb_context": bool(kb_section),
                "had_task_context": bool(task_section)
            }

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble analyzing the screen right now. Please try again in a moment.",
                "error": str(e)
            }
