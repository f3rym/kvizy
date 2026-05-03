from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.key_service import key_service
from src.services.claude_service import claude_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


class ClaudeStates(StatesGroup):
    """States for Claude interactions"""
    waiting_for_api_key = State()
    waiting_for_base_url = State()
    waiting_for_model = State()
    waiting_for_code = State()
    waiting_for_tool_confirmation = State()


@router.message(Command("api_key_add", "apikeyadd"))
async def api_key_add_handler(message: Message, state: FSMContext, user: User):
    """Add API key"""
    await state.set_state(ClaudeStates.waiting_for_api_key)
    await message.answer(
        "🔑 Отправьте ваш Claude API ключ.\n\n"
        "⚠️ Ключ будет зашифрован и сохранен безопасно.\n"
        "Сообщение с ключом будет автоматически удалено.\n\n"
        "Формат: sk-ant-xxxxx"
    )


@router.message(ClaudeStates.waiting_for_api_key)
async def api_key_receive_handler(message: Message, state: FSMContext, user: User):
    """Receive API key and ask for base URL"""
    api_key = message.text.strip()

    # Delete message with API key for security
    try:
        await message.delete()
    except:
        pass

    # Validate key format (basic check)
    if not api_key.startswith("sk-"):
        await message.answer("❌ Неверный формат API ключа. Ключ должен начинаться с 'sk-'")
        await state.clear()
        return

    # Save API key to state
    await state.update_data(api_key=api_key)

    # Ask for base URL
    await state.set_state(ClaudeStates.waiting_for_base_url)
    await message.answer(
        "🌐 Отправьте Base URL (или отправьте '-' для использования стандартного).\n\n"
        "Пример: http://157.230.181.250:20128/v1\n"
        "Или просто: -"
    )


@router.message(ClaudeStates.waiting_for_base_url)
async def base_url_receive_handler(message: Message, state: FSMContext, user: User):
    """Receive base URL and ask for model"""
    base_url = message.text.strip()

    # If user sends '-', use None (default)
    if base_url == '-':
        base_url = None

    # Save base URL to state
    await state.update_data(base_url=base_url)

    # Ask for model
    await state.set_state(ClaudeStates.waiting_for_model)
    await message.answer(
        "🤖 Отправьте название модели (или отправьте '-' для claude-sonnet-4-6).\n\n"
        "Примеры:\n"
        "• kr/claude-sonnet-4.5\n"
        "• claude-opus-4-7\n"
        "• claude-sonnet-4-6\n"
        "Или просто: -"
    )


@router.message(ClaudeStates.waiting_for_model)
async def model_receive_handler(message: Message, state: FSMContext, user: User):
    """Receive model and save all config"""
    model = message.text.strip()

    # If user sends '-', use default
    if model == '-':
        model = 'claude-sonnet-4-6'

    # Get saved data from state
    data = await state.get_data()
    api_key = data.get('api_key')
    base_url = data.get('base_url')

    # Save config
    success = await key_service.save_key(user.id, api_key, base_url, model)

    if success:
        masked = key_service.mask_key(api_key)
        config_text = f"✅ Конфигурация сохранена:\n\n"
        config_text += f"API ключ: {masked}\n"
        config_text += f"Base URL: {base_url or 'стандартный'}\n"
        config_text += f"Модель: {model}"
        await message.answer(config_text)
    else:
        await message.answer("❌ Ошибка при сохранении конфигурации")

    await state.clear()


@router.message(Command("api_key_show", "apikeyshow"))
async def api_key_show_handler(message: Message, user: User):
    """Show masked API key and config"""
    config = await key_service.get_config(user.id)

    if not config:
        await message.answer("❌ У вас нет сохраненной конфигурации. Используйте /api_key_add")
        return

    masked = key_service.mask_key(config['api_key'])
    config_text = f"🔑 Ваша конфигурация Claude:\n\n"
    config_text += f"API ключ: {masked}\n"
    config_text += f"Base URL: {config['base_url'] or 'стандартный'}\n"
    config_text += f"Модель: {config['model']}"

    await message.answer(config_text)


@router.message(Command("api_key_remove", "apikeyremove"))
async def api_key_remove_handler(message: Message, user: User):
    """Remove API key"""
    success = await key_service.delete_key(user.id)

    if success:
        await message.answer("✅ API ключ удален")
    else:
        await message.answer("❌ Ошибка при удалении ключа")


@router.message(Command("ask"))
async def ask_handler(message: Message, user: User, state: FSMContext):
    """Ask Claude a question"""
    # Check if user has config
    config = await key_service.get_config(user.id)
    if not config:
        await message.answer(
            "❌ Сначала добавьте конфигурацию: /api_key_add\n\n"
            "Получить ключ можно на https://console.anthropic.com/"
        )
        return

    # Get prompt from message
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("Использование: /ask <ваш вопрос>")
        return

    # Ask for confirmation to enable tools
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Разрешить выполнение команд", callback_data="ask_enable_tools"),
            InlineKeyboardButton(text="❌ Только текст", callback_data="ask_disable_tools")
        ]
    ])

    # Save prompt to state
    await state.update_data(prompt=prompt, config=config)
    await state.set_state(ClaudeStates.waiting_for_tool_confirmation)

    logger.info(f"Sending confirmation buttons for user {user.id}")
    await message.answer(
        "🤖 Claude может выполнять bash команды для ответа на ваш вопрос.\n\n"
        "Разрешить выполнение команд?",
        reply_markup=keyboard
    )
    logger.info("Confirmation buttons sent")


@router.callback_query(lambda c: c.data in ["ask_enable_tools", "ask_disable_tools"])
async def ask_confirmation_handler(callback: CallbackQuery, state: FSMContext, user: User):
    """Handle tool confirmation"""
    enable_tools = callback.data == "ask_enable_tools"

    # Get data from state
    data = await state.get_data()
    prompt = data.get('prompt')
    config = data.get('config')

    await state.clear()

    # Delete confirmation message
    await callback.message.delete()

    # Send "thinking" message
    status_msg = await callback.message.answer("🤔 Думаю...")

    try:
        # Query Claude with user_id for conversation history
        response = await claude_service.query(
            prompt,
            config['api_key'],
            user.id,
            config['model'],
            config['base_url'],
            enable_tools=enable_tools
        )

        # Delete status message
        await status_msg.delete()

        # Check if response is command confirmation request
        try:
            import json
            response_data = json.loads(response)
            if response_data.get("type") == "command_confirmation":
                # Show commands for confirmation
                text = response_data.get("text", "Хочу выполнить команду:")
                commands = response_data.get("commands", [])

                commands_text = "\n\n".join([f"```bash\n{cmd['command']}\n```" for cmd in commands])

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Выполнить", callback_data="execute_commands"),
                        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_commands")
                    ]
                ])

                await callback.message.answer(
                    f"{text}\n\n{commands_text}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
        except (json.JSONDecodeError, KeyError):
            pass

        # Send response (split if too long)
        if len(response) <= 4000:
            await callback.message.answer(response)
        else:
            # Split into chunks
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await callback.message.answer(chunk)

    except Exception as e:
        await status_msg.delete()
        await callback.message.answer(f"❌ Ошибка: {str(e)}")
        logger.error(f"Error in ask command: {e}")

    await callback.answer()


@router.callback_query(lambda c: c.data in ["execute_commands", "cancel_commands"])
async def command_execution_handler(callback: CallbackQuery, user: User):
    """Handle command execution confirmation"""
    if callback.data == "cancel_commands":
        await callback.message.edit_text("❌ Выполнение отменено")
        await callback.answer()
        return

    # Execute commands
    await callback.message.edit_text("⚙️ Выполняю команды...")

    try:
        config = await key_service.get_config(user.id)
        if not config:
            await callback.message.edit_text("❌ Конфигурация не найдена")
            await callback.answer()
            return

        result = await claude_service.execute_confirmed_commands(
            user.id,
            config['api_key'],
            config['model'],
            config['base_url']
        )

        logger.info(f"Got result from execute_confirmed_commands: {len(result)} chars")
        logger.info(f"Result preview: {result[:200]}")

        # Check if result is another command confirmation request
        try:
            import json
            response_data = json.loads(result)
            if response_data.get("type") == "command_confirmation":
                # Delete previous message
                await callback.message.delete()

                # Show new commands for confirmation
                text = response_data.get("text", "Хочу выполнить еще команды:")
                commands = response_data.get("commands", [])

                commands_text = "\n\n".join([f"```bash\n{cmd['command']}\n```" for cmd in commands])

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Выполнить", callback_data="execute_commands"),
                        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_commands")
                    ]
                ])

                await callback.message.answer(
                    f"{text}\n\n{commands_text}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                await callback.answer()
                return
        except (json.JSONDecodeError, KeyError):
            pass

        # Send result
        if len(result) <= 4000:
            await callback.message.answer(result)
        else:
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await callback.message.answer(chunk)

        await callback.message.delete()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        logger.error(f"Error executing commands: {e}")

    await callback.answer()


@router.message(Command("analyze"))
async def analyze_handler(message: Message, user: User):
    """Analyze code"""
    # Check config
    config = await key_service.get_config(user.id)
    if not config:
        await message.answer("❌ Сначала добавьте конфигурацию: /api_key_add")
        return

    # Get code from message
    code = message.text.replace("/analyze", "").strip()
    if not code:
        await message.answer(
            "Использование: /analyze <код>\n\n"
            "Или отправьте код в следующем сообщении"
        )
        return

    status_msg = await message.answer("🔍 Анализирую код...")

    try:
        response = await claude_service.analyze_code(
            code,
            config['api_key'],
            config['base_url'],
            config['model']
        )
        await status_msg.delete()
        await message.answer(response)
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("review"))
async def review_handler(message: Message, user: User):
    """Review code"""
    config = await key_service.get_config(user.id)
    if not config:
        await message.answer("❌ Сначала добавьте конфигурацию: /api_key_add")
        return

    code = message.text.replace("/review", "").strip()
    if not code:
        await message.answer("Использование: /review <код>")
        return

    status_msg = await message.answer("📝 Делаю code review...")

    try:
        response = await claude_service.review_code(
            code,
            config['api_key'],
            config['base_url'],
            config['model']
        )
        await status_msg.delete()
        await message.answer(response)
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("fix"))
async def fix_handler(message: Message, user: User):
    """Fix code"""
    config = await key_service.get_config(user.id)
    if not config:
        await message.answer("❌ Сначала добавьте конфигурацию: /api_key_add")
        return

    code = message.text.replace("/fix", "").strip()
    if not code:
        await message.answer("Использование: /fix <код>")
        return

    status_msg = await message.answer("🔧 Исправляю код...")

    try:
        response = await claude_service.fix_code(
            code,
            config['api_key'],
            config['base_url'],
            config['model']
        )
        await status_msg.delete()
        await message.answer(response)
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("clear", "clearhistory"))
async def clear_history_handler(message: Message, user: User):
    """Clear conversation history"""
    try:
        await claude_service.clear_conversation_history(user.id)
        await message.answer("✅ История диалога очищена")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        logger.error(f"Error clearing history: {e}")
