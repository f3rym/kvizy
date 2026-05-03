import anthropic
import subprocess
import json
from typing import Optional, List, Dict
from src.utils.logger import logger
from src.services.cache_service import cache_service


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.default_model = "claude-sonnet-4-6"
        self.timeout = 60  # seconds
        self.max_history = 10  # Maximum messages to keep in history

    async def get_conversation_history(self, user_id: int) -> List[Dict]:
        """Get conversation history for user from Redis"""
        try:
            key = f"conversation:{user_id}"
            history_json = await cache_service.redis_client.get(key)
            if history_json:
                return json.loads(history_json)
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def save_conversation_history(self, user_id: int, history: List[Dict]):
        """Save conversation history to Redis"""
        try:
            key = f"conversation:{user_id}"
            # Keep only last max_history messages
            if len(history) > self.max_history * 2:  # *2 because user+assistant pairs
                history = history[-(self.max_history * 2):]

            await cache_service.redis_client.set(key, json.dumps(history), ex=3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")

    async def clear_conversation_history(self, user_id: int):
        """Clear conversation history for user"""
        try:
            key = f"conversation:{user_id}"
            await cache_service.redis_client.delete(key)
            logger.info(f"Cleared conversation history for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")

    async def execute_confirmed_commands(self, user_id: int, api_key: str, model: str, base_url: Optional[str] = None) -> str:
        """Execute previously confirmed commands and get Claude's analysis"""
        try:
            # Get pending tools from cache
            pending_json = await cache_service.redis_client.get(f"pending_tools:{user_id}")
            if not pending_json:
                return "Нет команд для выполнения"

            pending = json.loads(pending_json)
            prompt = pending["prompt"]
            commands = pending["commands"]
            text = pending.get("text", "")

            # Create Anthropic client
            if base_url:
                client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            else:
                client = anthropic.Anthropic(api_key=api_key)

            # Get conversation history
            history = await self.get_conversation_history(user_id)

            # Build messages: history + user prompt
            messages = history + [{"role": "user", "content": prompt}]

            # Execute commands and build tool results
            tool_results = []
            for cmd in commands:
                output = await self._execute_bash(cmd["command"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": cmd["id"],
                    "content": output
                })

            # Build assistant message with tool use blocks
            from anthropic.types import TextBlock, ToolUseBlock
            assistant_content = []
            if text:
                assistant_content.append(TextBlock(type="text", text=text))

            for cmd in commands:
                assistant_content.append(ToolUseBlock(
                    type="tool_use",
                    id=cmd["id"],
                    name="bash",
                    input={"command": cmd["command"]}
                ))

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Get Claude's analysis of the results
            tools = [{
                "name": "bash",
                "description": "Execute bash commands on the host system. You have access to kubectl, docker, and the filesystem. Use /home/claude as your persistent workspace - files created there will persist between conversations. You can create projects, save code, and organize work in /home/claude.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute (e.g., 'kubectl get pods', 'ls /home/claude', 'cat /home/claude/project/file.py')"
                        }
                    },
                    "required": ["command"]
                }
            }]

            final_response = client.messages.create(
                model=model,
                max_tokens=4000,
                messages=messages,
                tools=tools
            )

            # Check if Claude wants to execute more commands
            if final_response.stop_reason == "tool_use":
                # Extract new commands that need confirmation
                new_commands = []
                for block in final_response.content:
                    if block.type == "tool_use" and block.name == "bash":
                        new_commands.append({
                            "id": block.id,
                            "command": block.input["command"]
                        })

                if new_commands:
                    # Extract text response
                    text_response = ""
                    for block in final_response.content:
                        if hasattr(block, 'text'):
                            text_response += block.text

                    # Update conversation history with previous interaction
                    new_history = history + [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": assistant_content},
                        {"role": "user", "content": tool_results}
                    ]
                    await self.save_conversation_history(user_id, new_history)

                    # Store new pending commands
                    await cache_service.redis_client.set(
                        f"pending_tools:{user_id}",
                        json.dumps({
                            "prompt": "",  # Empty since we're continuing
                            "commands": new_commands,
                            "text": text_response,
                            "model": model,
                            "base_url": base_url
                        }),
                        ex=300
                    )

                    # Return command confirmation request
                    return json.dumps({
                        "type": "command_confirmation",
                        "text": text_response or "Хочу выполнить еще команды:",
                        "commands": new_commands
                    })

            # Extract final text
            final_text = ""
            for block in final_response.content:
                if hasattr(block, 'text'):
                    final_text += block.text

            logger.info(f"Final response from Claude: {len(final_text)} chars")
            logger.info(f"Final response preview: {final_text[:200]}")

            # Save to history
            new_history = history + [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": final_text}
            ]
            await self.save_conversation_history(user_id, new_history)

            # Clear pending tools
            await cache_service.redis_client.delete(f"pending_tools:{user_id}")

            return final_text

        except Exception as e:
            logger.error(f"Error executing confirmed commands: {e}")
            raise

    async def _execute_bash(self, command: str) -> str:
        """Execute bash command and return output"""
        try:
            logger.info(f"Executing bash command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout if result.stdout else result.stderr
            logger.info(f"Command output: {output[:200]}")
            return output or "Command executed successfully (no output)"

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return f"Error: {str(e)}"

    async def query(
        self,
        prompt: str,
        api_key: str,
        user_id: int,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        enable_tools: bool = True
    ) -> str:
        """
        Send a query to Claude API with optional tool use and conversation history

        Args:
            prompt: The prompt to send
            api_key: Claude API key
            user_id: User ID for conversation history
            model: Model to use (default: claude-sonnet-4-6)
            base_url: Optional custom base URL
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            enable_tools: Enable bash command execution

        Returns:
            Claude's response
        """
        if not model:
            model = self.default_model

        logger.info(f"Sending query to Claude (model={model}, user={user_id}, tools={enable_tools})")

        try:
            # Create Anthropic client
            if base_url:
                client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            else:
                client = anthropic.Anthropic(api_key=api_key)

            # Get conversation history
            history = await self.get_conversation_history(user_id)

            # Define tools
            tools = []
            if enable_tools:
                tools = [
                    {
                        "name": "bash",
                        "description": "Execute bash commands on the host system. You have access to kubectl, docker, and the filesystem. Use /home/claude as your persistent workspace - files created there will persist between conversations. You can create projects, save code, and organize work in /home/claude.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The bash command to execute (e.g., 'kubectl get pods', 'ls /home/claude', 'cat /home/claude/project/file.py')"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                ]

            # Build messages from history + new prompt
            messages = history + [{"role": "user", "content": prompt}]

            # Tool use loop
            final_response = ""
            while True:
                if tools:
                    response = client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=messages,
                        tools=tools
                    )
                else:
                    response = client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=messages
                    )

                # Check if we need to process tool calls
                if response.stop_reason == "tool_use":
                    # Extract commands that need confirmation
                    commands_to_confirm = []
                    for block in response.content:
                        if block.type == "tool_use" and block.name == "bash":
                            commands_to_confirm.append({
                                "id": block.id,
                                "command": block.input["command"]
                            })

                    # Always return commands for user confirmation
                    if commands_to_confirm:
                        # Extract any text response before tool use
                        text_response = ""
                        for block in response.content:
                            if hasattr(block, 'text'):
                                text_response += block.text

                        # Store simplified state for later
                        await cache_service.redis_client.set(
                            f"pending_tools:{user_id}",
                            json.dumps({
                                "prompt": prompt,
                                "commands": commands_to_confirm,
                                "text": text_response,
                                "model": model,
                                "base_url": base_url
                            }),
                            ex=300  # 5 minutes
                        )

                        return json.dumps({
                            "type": "command_confirmation",
                            "text": text_response or "Хочу выполнить команду:",
                            "commands": commands_to_confirm
                        })

                    # If no bash commands, just break (shouldn't happen)
                    break
                else:
                    # Extract final text response
                    for block in response.content:
                        if hasattr(block, 'text'):
                            final_response += block.text

                    logger.info(f"Claude response received ({len(final_response)} chars)")

                    # Save conversation history (user prompt + assistant response)
                    new_history = history + [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": final_response}
                    ]
                    await self.save_conversation_history(user_id, new_history)

                    return final_response

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise Exception(f"Claude API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error querying Claude: {e}")
            raise

    async def analyze_code(self, code: str, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None, language: str = "python") -> str:
        """Analyze code with Claude"""
        prompt = f"""Проанализируй этот код на {language}:

```{language}
{code}
```

Предоставь:
1. Краткое описание что делает код
2. Потенциальные проблемы или баги
3. Рекомендации по улучшению
4. Оценка качества кода (1-10)
"""
        return await self.query(prompt, api_key, model, base_url, enable_tools=False)

    async def review_code(self, code: str, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None, language: str = "python") -> str:
        """Review code with Claude"""
        prompt = f"""Сделай code review для этого кода на {language}:

```{language}
{code}
```

Проверь:
- Безопасность (SQL injection, XSS, etc.)
- Производительность
- Читаемость
- Соответствие best practices
- Потенциальные баги

Укажи severity для каждой проблемы: CRITICAL, WARNING, INFO
"""
        return await self.query(prompt, api_key, model, base_url, enable_tools=False)

    async def fix_code(self, code: str, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None, language: str = "python") -> str:
        """Suggest fixes for code"""
        prompt = f"""Найди и исправь проблемы в этом коде на {language}:

```{language}
{code}
```

Предоставь:
1. Список найденных проблем
2. Исправленный код
3. Объяснение изменений
"""
        return await self.query(prompt, api_key, model, base_url, enable_tools=False)


# Global Claude service instance
claude_service = ClaudeService()
