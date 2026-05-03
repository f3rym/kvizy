from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

from src.services.cache_service import cache_service
from src.services.claude_service import claude_service
from src.services.key_service import key_service
from src.utils.logger import logger


class SchedulerService:
    """Service for managing scheduled tasks and reminders"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.bot = None  # Will be set from main.py

    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Scheduler service started")

    async def restore_jobs(self):
        """Restore jobs from Redis on startup"""
        try:
            # Get all job info keys from Redis
            pattern = "job_info:*"
            keys = await cache_service.redis_client.keys(pattern)

            restored_count = 0
            for key in keys:
                try:
                    job_json = await cache_service.redis_client.get(key)
                    if not job_json:
                        continue

                    job_info = json.loads(job_json)
                    # Parse key to get user_id and task_id
                    # Format: job_info:user_id:task_id
                    key_str = key.decode() if isinstance(key, bytes) else key
                    parts = key_str.split(":")
                    if len(parts) != 3:
                        continue

                    user_id = int(parts[1])
                    task_id = parts[2]

                    job_type = job_info.get("type")
                    prompt = job_info.get("prompt")

                    if job_type == "cron":
                        cron_expression = job_info.get("cron_expression")
                        if cron_expression and prompt:
                            parts = cron_expression.split()
                            if len(parts) == 5:
                                minute, hour, day, month, day_of_week = parts
                                self.scheduler.add_job(
                                    self._execute_scheduled_task,
                                    trigger=CronTrigger(
                                        minute=minute,
                                        hour=hour,
                                        day=day,
                                        month=month,
                                        day_of_week=day_of_week
                                    ),
                                    args=[user_id, task_id, prompt],
                                    id=f"cron_{user_id}_{task_id}",
                                    replace_existing=True
                                )
                                restored_count += 1
                                logger.info(f"Restored cron job: {task_id} for user {user_id}")

                    elif job_type == "reminder":
                        run_date_str = job_info.get("run_date")
                        if run_date_str and prompt:
                            from datetime import datetime
                            run_date = datetime.fromisoformat(run_date_str)
                            # Only restore if in the future
                            if run_date > datetime.now():
                                self.scheduler.add_job(
                                    self._execute_scheduled_task,
                                    trigger=DateTrigger(run_date=run_date),
                                    args=[user_id, task_id, prompt],
                                    id=f"reminder_{user_id}_{task_id}",
                                    replace_existing=True
                                )
                                restored_count += 1
                                logger.info(f"Restored reminder: {task_id} for user {user_id}")
                            else:
                                # Remove expired reminder
                                await cache_service.redis_client.delete(key)
                                logger.info(f"Removed expired reminder: {task_id}")

                except Exception as e:
                    logger.error(f"Error restoring job from {key}: {e}")
                    continue

            logger.info(f"Restored {restored_count} scheduled jobs from Redis")

        except Exception as e:
            logger.error(f"Error restoring jobs: {e}")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler service stopped")

    def set_bot(self, bot):
        """Set bot instance for sending messages"""
        self.bot = bot

    async def _execute_scheduled_task(self, user_id: int, task_id: str, prompt: str):
        """Execute a scheduled task"""
        try:
            logger.info(f"Executing scheduled task {task_id} for user {user_id}")

            # Get user config
            config = await key_service.get_config(user_id)
            if not config:
                logger.error(f"No config found for user {user_id}")
                return

            # Get user's telegram_id for sending messages
            from src.services.auth_service import auth_service
            user = await auth_service.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return

            telegram_id = user.telegram_id

            # Query Claude
            response = await claude_service.query(
                prompt,
                config['api_key'],
                user_id,
                config['model'],
                config['base_url'],
                enable_tools=True
            )

            # Send response to user
            if self.bot:
                # Check if response is command confirmation
                try:
                    response_data = json.loads(response)
                    if response_data.get("type") == "command_confirmation":
                        # For scheduled tasks, auto-execute commands
                        result = await claude_service.execute_confirmed_commands(
                            user_id,
                            config['api_key'],
                            config['model'],
                            config['base_url']
                        )
                        await self.bot.send_message(telegram_id, f"🔔 Scheduled task: {task_id}\n\n{result}")
                    else:
                        await self.bot.send_message(telegram_id, f"🔔 Scheduled task: {task_id}\n\n{response}")
                except (json.JSONDecodeError, KeyError):
                    await self.bot.send_message(telegram_id, f"🔔 Scheduled task: {task_id}\n\n{response}")

        except Exception as e:
            logger.error(f"Error executing scheduled task {task_id}: {e}")
            if self.bot and telegram_id:
                try:
                    await self.bot.send_message(telegram_id, f"❌ Error in scheduled task {task_id}: {str(e)}")
                except:
                    pass

    async def add_cron_job(
        self,
        user_id: int,
        task_id: str,
        prompt: str,
        cron_expression: str,
        description: str = ""
    ) -> bool:
        """
        Add a cron job

        Args:
            user_id: User ID
            task_id: Unique task ID
            prompt: Prompt to send to Claude
            cron_expression: Cron expression (e.g., "*/5 * * * *" for every 5 minutes)
            description: Task description

        Returns:
            True if successful
        """
        try:
            # Parse cron expression (minute hour day month day_of_week)
            parts = cron_expression.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False

            minute, hour, day, month, day_of_week = parts

            # Add job to scheduler
            self.scheduler.add_job(
                self._execute_scheduled_task,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                args=[user_id, task_id, prompt],
                id=f"cron_{user_id}_{task_id}",
                replace_existing=True
            )

            # Save to Redis
            await self._save_job_info(user_id, task_id, {
                "type": "cron",
                "prompt": prompt,
                "cron_expression": cron_expression,
                "description": description,
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"Added cron job {task_id} for user {user_id}: {cron_expression}")
            return True

        except Exception as e:
            logger.error(f"Error adding cron job: {e}")
            return False

    async def add_reminder(
        self,
        user_id: int,
        task_id: str,
        prompt: str,
        run_date: datetime,
        description: str = ""
    ) -> bool:
        """
        Add a one-time reminder

        Args:
            user_id: User ID
            task_id: Unique task ID
            prompt: Prompt to send to Claude
            run_date: When to run the reminder
            description: Task description

        Returns:
            True if successful
        """
        try:
            # Add job to scheduler
            self.scheduler.add_job(
                self._execute_scheduled_task,
                trigger=DateTrigger(run_date=run_date),
                args=[user_id, task_id, prompt],
                id=f"reminder_{user_id}_{task_id}",
                replace_existing=True
            )

            # Save to Redis
            await self._save_job_info(user_id, task_id, {
                "type": "reminder",
                "prompt": prompt,
                "run_date": run_date.isoformat(),
                "description": description,
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"Added reminder {task_id} for user {user_id} at {run_date}")
            return True

        except Exception as e:
            logger.error(f"Error adding reminder: {e}")
            return False

    async def remove_job(self, user_id: int, task_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            # Try both cron and reminder prefixes
            for prefix in ["cron", "reminder"]:
                job_id = f"{prefix}_{user_id}_{task_id}"
                try:
                    self.scheduler.remove_job(job_id)
                    await self._delete_job_info(user_id, task_id)
                    logger.info(f"Removed job {task_id} for user {user_id}")
                    return True
                except:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error removing job: {e}")
            return False

    async def list_jobs(self, user_id: int) -> List[Dict]:
        """List all jobs for a user"""
        try:
            jobs = []
            # Get all job info from Redis
            pattern = f"job_info:{user_id}:*"
            keys = await cache_service.redis_client.keys(pattern)

            for key in keys:
                job_json = await cache_service.redis_client.get(key)
                if job_json:
                    job_info = json.loads(job_json)
                    task_id = key.decode().split(":")[-1]
                    job_info["task_id"] = task_id
                    jobs.append(job_info)

            return jobs

        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []

    async def _save_job_info(self, user_id: int, task_id: str, info: Dict):
        """Save job info to Redis"""
        key = f"job_info:{user_id}:{task_id}"
        await cache_service.redis_client.set(key, json.dumps(info))

    async def _delete_job_info(self, user_id: int, task_id: str):
        """Delete job info from Redis"""
        key = f"job_info:{user_id}:{task_id}"
        await cache_service.redis_client.delete(key)


# Global scheduler service instance
scheduler_service = SchedulerService()
