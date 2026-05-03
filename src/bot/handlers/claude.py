from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
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
    waiting_for_code = State()


@router.message(Command("api_key_add"))
async def api_key_add_handler(message: Message, state: FSMContext, user: User):
    """Add API key"""
    await state.set_state(ClaudeStates.waiting_for_api_key)
    await message.answer(
        "🔑 Отправьте ваш Claude API ключ.\n\n"
        "⚠️ Ключ будет зашифрован и сохранен безопасно.\n"
        "Сообщение с ключом будет автоматически удалено."
    )


@router.message(ClaudeStates.waiting_for_api_key)
async def api_key_receive_handler(message: Message, state: FSMContext, user: User):
    """Receive and save API key"""
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

    # Save key
    success = await key_service.save_key(user.id, api_key)

    if success:
        masked = key_service.mask_key(api_key)
        await message.answer(f"✅ API ключ сохранен: {masked}")
    else:
        await message.answer("❌ Ошибка при сохранении ключа")

    await state.clear()


@router.message(Command("api_key_show"))
async def api_key_show_handler(message: Message, user: User):
    """Show masked API key"""
    api_key = await key_service.get_key(user.id)

    if not api_key:
        await message.answer("❌ У вас нет сохраненного API ключа. Используйте /api_key_add")
        return

    masked = key_service.mask_key(api_key)
    await message.answer(f"🔑 Ваш API ключ: {masked}")


@router.message(Command("api_key_remove"))
async def api_key_remove_handler(message: Message, user: User):
    """Remove API key"""
    success = await key_service.delete_key(user.id)

    if success:
        await message.answer("✅ API ключ удален")
    else:
        await message.answer("❌ Ошибка при удалении ключа")


@router.message(Command("ask"))
async def ask_handler(message: Message, user: User):
    """Ask Claude a question"""
    # Check if user has API key
    api_key = await key_service.get_key(user.id)
    if not api_key:
        await message.answer(
            "❌ Сначала добавьте API ключ: /api_key_add\n\n"
            "Получить ключ можно на https://console.anthropic.com/"
        )
        return

    # Get prompt from message
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("Использование: /ask <ваш вопрос>")
        return

    # Send "thinking" message
    status_msg = await message.answer("🤔 Думаю...")

    try:
        # Query Claude
        response = await claude_service.query(prompt, api_key)

        # Delete status message
        await status_msg.delete()

        # Send response (split if too long)
        if len(response) <= 4000:
            await message.answer(response)
        else:
            # Split into chunks
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await message.answer(chunk)

    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")
        logger.error(f"Error in ask command: {e}")


@router.message(Command("analyze"))
async def analyze_handler(message: Message, user: User):
    """Analyze code"""
    # Check API key
    api_key = await key_service.get_key(user.id)
    if not api_key:
        await message.answer("❌ Сначала добавьте API ключ: /api_key_add")
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
        response = await claude_service.analyze_code(code, api_key)
        await status_msg.delete()
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("review"))
async def review_handler(message: Message, user: User):
    """Review code"""
    api_key = await key_service.get_key(user.id)
    if not api_key:
        await message.answer("❌ Сначала добавьте API ключ: /api_key_add")
        return

    code = message.text.replace("/review", "").strip()
    if not code:
        await message.answer("Использование: /review <код>")
        return

    status_msg = await message.answer("📝 Делаю code review...")

    try:
        response = await claude_service.review_code(code, api_key)
        await status_msg.delete()
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("fix"))
async def fix_handler(message: Message, user: User):
    """Fix code"""
    api_key = await key_service.get_key(user.id)
    if not api_key:
        await message.answer("❌ Сначала добавьте API ключ: /api_key_add")
        return

    code = message.text.replace("/fix", "").strip()
    if not code:
        await message.answer("Использование: /fix <код>")
        return

    status_msg = await message.answer("🔧 Исправляю код...")

    try:
        response = await claude_service.fix_code(code, api_key)
        await status_msg.delete()
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}")
