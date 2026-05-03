from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
import redis.asyncio as redis

from src.services.file_service import file_service
from src.bot.states.file_states import FileStates
from src.models.user import User
from src.core.config import settings
from src.utils.logger import logger

router = Router()

# Redis client for storing current working directory
redis_client = None


async def get_redis():
    """Get Redis client"""
    global redis_client
    if not redis_client:
        redis_client = await redis.from_url(settings.redis_url)
    return redis_client


async def get_cwd(user_id: int) -> str:
    """Get current working directory for user"""
    r = await get_redis()
    cwd = await r.get(f"cwd:{user_id}")
    return cwd.decode() if cwd else "/app/data"


async def set_cwd(user_id: int, path: str):
    """Set current working directory for user"""
    r = await get_redis()
    await r.set(f"cwd:{user_id}", path)


@router.message(Command("ls"))
async def ls_handler(message: Message, user: User):
    """List files in current directory"""
    cwd = await get_cwd(user.telegram_id)

    try:
        files = await file_service.list_files(cwd)

        if not files:
            await message.answer(f"📁 {cwd}\n\nПусто")
            return

        text = f"📁 {cwd}\n\n"

        for f in files:
            emoji = "📁" if f['is_dir'] else "📄"
            size = f"{f['size']} bytes" if not f['is_dir'] else ""
            text += f"{emoji} {f['name']} {size}\n"

        await message.answer(text)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("pwd"))
async def pwd_handler(message: Message, user: User):
    """Show current working directory"""
    cwd = await get_cwd(user.telegram_id)
    await message.answer(f"📍 Текущая директория:\n{cwd}")


@router.message(Command("cd"))
async def cd_handler(message: Message, user: User):
    """Change directory"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /cd <путь>")
        return

    new_path = args[1]

    # Handle relative paths
    if not new_path.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        new_path = f"{cwd}/{new_path}"

    try:
        # Validate path exists and is directory
        if not file_service.validate_path(new_path):
            await message.answer("❌ Доступ запрещен")
            return

        import os
        if not os.path.exists(new_path):
            await message.answer("❌ Директория не найдена")
            return

        if not os.path.isdir(new_path):
            await message.answer("❌ Это не директория")
            return

        await set_cwd(user.telegram_id, new_path)
        await message.answer(f"✅ Перешли в: {new_path}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("cat"))
async def cat_handler(message: Message, user: User):
    """Read file content"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /cat <файл>")
        return

    file_path = args[1]

    # Handle relative paths
    if not file_path.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        file_path = f"{cwd}/{file_path}"

    try:
        content = await file_service.read_file(file_path)

        # Send as code block
        await message.answer(f"📄 {file_path}\n\n```\n{content}\n```", parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("mkdir"))
async def mkdir_handler(message: Message, user: User):
    """Create directory"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /mkdir <имя>")
        return

    dir_name = args[1]

    # Handle relative paths
    if not dir_name.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        dir_name = f"{cwd}/{dir_name}"

    try:
        await file_service.create_directory(dir_name)
        await message.answer(f"✅ Директория создана: {dir_name}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("create"))
async def create_handler(message: Message, state: FSMContext, user: User):
    """Create new file"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /create <имя файла>")
        return

    file_name = args[1]

    # Handle relative paths
    if not file_name.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        file_name = f"{cwd}/{file_name}"

    await state.update_data(file_path=file_name)
    await state.set_state(FileStates.waiting_for_file_content)
    await message.answer(f"📝 Отправьте содержимое файла {file_name}:")


@router.message(FileStates.waiting_for_file_content)
async def create_content_handler(message: Message, state: FSMContext, user: User):
    """Receive file content and create file"""
    data = await state.get_data()
    file_path = data['file_path']
    content = message.text

    try:
        await file_service.write_file(file_path, content)
        await message.answer(f"✅ Файл создан: {file_path}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

    await state.clear()


@router.message(Command("rm"))
async def rm_handler(message: Message, user: User):
    """Delete file with confirmation"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /rm <файл>")
        return

    file_path = args[1]

    # Handle relative paths
    if not file_path.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        file_path = f"{cwd}/{file_path}"

    # Show confirmation
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Удалить", callback_data=f"rm_confirm:{file_path}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="rm_cancel")
        ]
    ])

    await message.answer(
        f"⚠️ Удалить файл?\n{file_path}\n\nЭто действие нельзя отменить!",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("rm_confirm:"))
async def rm_confirm_handler(callback: CallbackQuery, user: User):
    """Confirm file deletion"""
    file_path = callback.data.replace("rm_confirm:", "")

    try:
        await file_service.delete_file(file_path)
        await callback.message.edit_text(f"✅ Файл удален: {file_path}")

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")

    await callback.answer()


@router.callback_query(F.data == "rm_cancel")
async def rm_cancel_handler(callback: CallbackQuery):
    """Cancel file deletion"""
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


@router.message(Command("download"))
async def download_handler(message: Message, user: User):
    """Download file from bot"""
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /download <файл>")
        return

    file_path = args[1]

    # Handle relative paths
    if not file_path.startswith('/'):
        cwd = await get_cwd(user.telegram_id)
        file_path = f"{cwd}/{file_path}"

    try:
        # Check file size (Telegram limit 50MB)
        import os
        size = os.path.getsize(file_path)
        if size > 50 * 1024 * 1024:
            await message.answer("❌ Файл слишком большой (макс 50MB)")
            return

        # Send file
        from aiogram.types import FSInputFile
        file = FSInputFile(file_path)
        await message.answer_document(file)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.document)
async def upload_handler(message: Message, user: User):
    """Upload file to bot"""
    document = message.document

    # Check size
    if document.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой (макс 20MB)")
        return

    cwd = await get_cwd(user.telegram_id)
    file_path = f"{cwd}/{document.file_name}"

    try:
        # Download file
        file = await message.bot.download(document)

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file.read())

        await message.answer(f"✅ Файл загружен: {file_path}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
