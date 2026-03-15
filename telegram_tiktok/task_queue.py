import asyncio

# Глобальная асинхронная очередь (инициализируется лениво)
_queue = None

def get_queue():
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue

async def add_to_queue(user_id: int, message_id: int, url: str, status_msg_id: int = None):
    task = {
        "user_id": user_id,
        "message_id": message_id,
        "url": url,
        "status_msg_id": status_msg_id
    }
    await get_queue().put(task)

async def get_from_queue():
    # Ждет появления задачи в очереди (не блокируя остальной код)
    task = await get_queue().get()
    return task

def task_done():
    # Отмечаем задачу как выполненную
    get_queue().task_done()
