import subprocess
import asyncio
from typing import Optional
from src.utils.logger import logger
from src.services.cache_service import cache_service


class ClaudeService:
    """Service for interacting with Claude CLI"""

    def __init__(self):
        self.default_model = "claude-sonnet-4-6"
        self.timeout = 60  # seconds

    async def query(
        self,
        prompt: str,
        api_key: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send a query to Claude CLI

        Args:
            prompt: The prompt to send
            api_key: Claude API key
            model: Model to use (default: claude-sonnet-4-6)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Claude's response
        """
        if not model:
            model = self.default_model

        logger.info(f"Sending query to Claude (model={model}, tokens={max_tokens})")

        # Check cache first
        cached = await cache_service.get(prompt, model)
        if cached:
            logger.info("Returning cached response")
            return cached

        # Build command
        cmd = [
            "claude",
            "--api-key", api_key,
            "--model", model,
            "--temperature", str(temperature),
            "--max-tokens", str(max_tokens),
            prompt
        ]

        try:
            # Execute command with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Claude query timed out after {self.timeout} seconds")

            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"Claude CLI error: {error_msg}")
                raise Exception(f"Claude CLI error: {error_msg}")

            response = stdout.decode('utf-8', errors='ignore').strip()
            logger.info(f"Claude response received ({len(response)} chars)")

            # Cache the response
            await cache_service.set(prompt, response, model)

            return response

        except FileNotFoundError:
            logger.error("Claude CLI not found")
            raise Exception("Claude CLI not installed. Please install it first.")
        except Exception as e:
            logger.error(f"Error querying Claude: {e}")
            raise

    async def analyze_code(self, code: str, api_key: str, language: str = "python") -> str:
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
        return await self.query(prompt, api_key)

    async def review_code(self, code: str, api_key: str, language: str = "python") -> str:
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
        return await self.query(prompt, api_key)

    async def fix_code(self, code: str, api_key: str, language: str = "python") -> str:
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
        return await self.query(prompt, api_key)


# Global Claude service instance
claude_service = ClaudeService()
