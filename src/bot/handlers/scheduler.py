from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from src.services.scheduler_service import scheduler_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


class SchedulerStates(StatesGroup):
    """States for scheduler interactions"""
    waiting_for_cron_expression = State()
    waiting_for_cron_prompt = State()
    waiting_for_reminder_time = State()
    waiting_for_reminder_prompt = State()


@router.message(Command("cron", "cronadd"))
async def cron_add_handler(message: Message, state: FSMContext, user: User):
    """Add a cron job"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_cron")]
    ])

    await message.answer(
        "⏰ Создание cron-задачи\n\n"
        "Отправьте cron выражение (5 полей: минута час день месяц день_недели)\n\n"
        "Примеры:\n"
        "• `*/5 * * * *` - каждые 5 минут\n"
        "• `0 */2 * * *` - каждые 2 часа\n"
        "• `0 9 * * 1-5` - в 9:00 по будням\n"
        "• `30 14 * * *` - каждый день в 14:30",
        reply_markup=keyboard
    )
    await state.set_state(SchedulerStates.waiting_for_cron_expression)


@router.callback_query(lambda c: c.data == "cancel_cron")
async def cancel_cron_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel cron creation"""
    await state.clear()
    await callback.message.edit_text("❌ Создание cron-задачи отменено")
    await callback.answer()


@router.message(SchedulerStates.waiting_for_cron_expression)
async def cron_expression_handler(message: Message, state: FSMContext, user: User):
    """Receive cron expression"""
    cron_expression = message.text.strip()

    # Validate cron expression
    parts = cron_expression.split()
    if len(parts) != 5:
        await message.answer("❌ Неверный формат. Нужно 5 полей: минута час день месяц день_недели")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_cron")]
    ])

    await state.update_data(cron_expression=cron_expression)
    await state.set_state(SchedulerStates.waiting_for_cron_prompt)
    await message.answer(
        "✅ Cron выражение принято\n\n"
        "Теперь отправьте задачу для Claude (что проверять/делать):\n\n"
        "Примеры:\n"
        "• Проверь статус подов в kubernetes\n"
        "• Проверь использование CPU и памяти\n"
        "• Проверь логи за последний час",
        reply_markup=keyboard
    )


@router.message(SchedulerStates.waiting_for_cron_prompt)
async def cron_prompt_handler(message: Message, state: FSMContext, user: User):
    """Receive cron prompt and create job"""
    prompt = message.text.strip()
    data = await state.get_data()
    cron_expression = data.get('cron_expression')

    # Generate task ID
    task_id = f"task_{int(datetime.now().timestamp())}"

    # Add cron job
    success = await scheduler_service.add_cron_job(
        user.id,
        task_id,
        prompt,
        cron_expression,
        description=prompt[:100]
    )

    if success:
        await message.answer(
            f"✅ Cron-задача создана!\n\n"
            f"ID: {task_id}\n"
            f"Расписание: {cron_expression}\n"
            f"Задача: {prompt}\n\n"
            f"Используйте /cronlist для просмотра всех задач"
        )
    else:
        await message.answer("❌ Ошибка при создании задачи")

    await state.clear()


@router.message(Command("reminder", "remind"))
async def reminder_add_handler(message: Message, state: FSMContext, user: User):
    """Add a reminder"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reminder")]
    ])

    await message.answer(
        "⏰ Создание напоминания\n\n"
        "Отправьте время в одном из форматов:\n\n"
        "• `5m` - через 5 минут\n"
        "• `2h` - через 2 часа\n"
        "• `1d` - через 1 день\n"
        "• `2026-05-03 18:30` - конкретное время",
        reply_markup=keyboard
    )
    await state.set_state(SchedulerStates.waiting_for_reminder_time)


@router.callback_query(lambda c: c.data == "cancel_reminder")
async def cancel_reminder_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel reminder creation"""
    await state.clear()
    await callback.message.edit_text("❌ Создание напоминания отменено")
    await callback.answer()


@router.message(SchedulerStates.waiting_for_reminder_time)
async def reminder_time_handler(message: Message, state: FSMContext, user: User):
    """Receive reminder time"""
    time_str = message.text.strip()

    try:
        # Parse time
        run_date = None

        # Relative time (5m, 2h, 1d)
        if time_str.endswith('m'):
            minutes = int(time_str[:-1])
            run_date = datetime.now() + timedelta(minutes=minutes)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            run_date = datetime.now() + timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            run_date = datetime.now() + timedelta(days=days)
        else:
            # Absolute time
            run_date = datetime.strptime(time_str, "%Y-%m-%d %H:%M")

        if run_date <= datetime.now():
            await message.answer("❌ Время должно быть в будущем")
            return

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reminder")]
        ])

        await state.update_data(run_date=run_date)
        await state.set_state(SchedulerStates.waiting_for_reminder_prompt)
        await message.answer(
            f"✅ Время установлено: {run_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Теперь отправьте задачу для Claude:\n\n"
            f"Примеры:\n"
            f"• Напомни проверить деплой\n"
            f"• Проверь статус сервисов\n"
            f"• Покажи метрики за день",
            reply_markup=keyboard
        )

    except ValueError:
        await message.answer("❌ Неверный формат времени")


@router.message(SchedulerStates.waiting_for_reminder_prompt)
async def reminder_prompt_handler(message: Message, state: FSMContext, user: User):
    """Receive reminder prompt and create reminder"""
    prompt = message.text.strip()
    data = await state.get_data()
    run_date = data.get('run_date')

    # Generate task ID
    task_id = f"reminder_{int(datetime.now().timestamp())}"

    # Add reminder
    success = await scheduler_service.add_reminder(
        user.id,
        task_id,
        prompt,
        run_date,
        description=prompt[:100]
    )

    if success:
        await message.answer(
            f"✅ Напоминание создано!\n\n"
            f"ID: {task_id}\n"
            f"Время: {run_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Задача: {prompt}\n\n"
            f"Используйте /cronlist для просмотра всех задач"
        )
    else:
        await message.answer("❌ Ошибка при создании напоминания")

    await state.clear()


@router.message(Command("cronlist", "schedulelist"))
async def cron_list_handler(message: Message, user: User):
    """List all scheduled jobs"""
    jobs = await scheduler_service.list_jobs(user.id)

    if not jobs:
        await message.answer("📋 У вас нет запланированных задач")
        return

    text = "📋 Ваши запланированные задачи:\n\n"

    # Create inline keyboard with delete buttons
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard_buttons = []

    for job in jobs:
        task_id = job.get('task_id', 'unknown')
        job_type = job.get('type', 'unknown')
        description = job.get('description', 'No description')
        created_at = job.get('created_at', '')

        if job_type == 'cron':
            cron_expr = job.get('cron_expression', '')
            text += f"🔄 {task_id}\n"
            text += f"   Тип: Cron\n"
            text += f"   Расписание: {cron_expr}\n"
            text += f"   Задача: {description}\n\n"
        elif job_type == 'reminder':
            run_date = job.get('run_date', '')
            text += f"⏰ {task_id}\n"
            text += f"   Тип: Напоминание\n"
            text += f"   Время: {run_date}\n"
            text += f"   Задача: {description}\n\n"

        # Add delete button for each task
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"🗑 Удалить {task_id}",
                callback_data=f"delete_task_{task_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("delete_task_"))
async def delete_task_callback(callback: CallbackQuery, user: User):
    """Handle task deletion via button"""
    task_id = callback.data.replace("delete_task_", "")

    success = await scheduler_service.remove_job(user.id, task_id)

    if success:
        await callback.message.edit_text(f"✅ Задача {task_id} удалена")
    else:
        await callback.message.edit_text(f"❌ Задача {task_id} не найдена")

    await callback.answer()


@router.message(Command("cronremove", "scheduleremove"))
async def cron_remove_handler(message: Message, user: User):
    """Remove a scheduled job"""
    # Get task_id from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /cronremove <task_id>")
        return

    task_id = parts[1].strip()

    success = await scheduler_service.remove_job(user.id, task_id)

    if success:
        await message.answer(f"✅ Задача {task_id} удалена")
    else:
        await message.answer(f"❌ Задача {task_id} не найдена")
