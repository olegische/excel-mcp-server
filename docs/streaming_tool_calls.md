# Потоковая передача результатов вызовов инструментов в FastMCP

Я провел анализ реализации сервера FastMCP, в частности файлов `.venv/lib/python3.10/site-packages/mcp/server/fastmcp/server.py` и `.venv/lib/python3.10/site-packages/mcp/server/sse.py`, чтобы определить, возможна ли потоковая передача результатов вызовов инструментов (tool calls) частями.

## Текущая реализация `call_tool`

Метод `call_tool` в `mcp/server/fastmcp/server.py` отвечает за выполнение зарегистрированных инструментов и возврат их результатов. Его сигнатура выглядит следующим образом:

```python
# .venv/lib/python3.10/site-packages/mcp/server/fastmcp/server.py
async def call_tool(
    self, name: str, arguments: dict[str, Any]
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Call a tool by name with arguments."""
    context = self.get_context()
    result = await self._tool_manager.call_tool(name, arguments, context=context)
    converted_result = _convert_to_content(result)
    return converted_result
```

Как видно, этот метод возвращает `Sequence[TextContent | ImageContent | EmbeddedResource]`. Это означает, что:
1.  Вызов инструмента (`self._tool_manager.call_tool`) выполняется полностью.
2.  Полученный `result` затем преобразуется в конечную последовательность объектов контента с помощью функции `_convert_to_content`.
3.  Только после того, как весь результат инструмента будет собран в эту последовательность, он возвращается.

Функция `_convert_to_content` дополнительно подтверждает это поведение, обрабатывая результат в единый, завершенный набор контента:

```python
# .venv/lib/python3.10/site-packages/mcp/server/fastmcp/server.py
def _convert_to_content(
    result: Any,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Convert a result to a sequence of content objects."""
    if result is None:
        return []

    if isinstance(result, TextContent | ImageContent | EmbeddedResource):
        return [result]

    # ... (другая логика преобразования) ...

    if not isinstance(result, str):
        result = pydantic_core.to_json(result, fallback=str, indent=2).decode()

    return [TextContent(type="text", text=result)]
```

Таким образом, на уровне `FastMCP` вызов инструмента является синхронной операцией, которая возвращает полный результат, а не поток частичных данных.

## Роль SSE в FastMCP

Файл `mcp/server/sse.py` демонстрирует, что FastMCP использует Server-Sent Events (SSE) для обмена сообщениями между сервером и клиентом. Это позволяет серверу отправлять асинхронные уведомления клиенту, такие как:

*   **Обновления прогресса:** `ctx.report_progress` в объекте `Context` использует SSE для отправки уведомлений о ходе выполнения.
*   **Логи:** `ctx.log` (и его удобные обертки `ctx.info`, `ctx.debug` и т.д.) также используют SSE для отправки логов клиенту.

Пример из `mcp/server/sse.py` показывает, как сообщения отправляются через SSE:

```python
# .venv/lib/python3.10/site-packages/mcp/server/sse.py
async def sse_writer():
    logger.debug("Starting SSE writer")
    async with sse_stream_writer, write_stream_reader:
        await sse_stream_writer.send(
            {"event": "endpoint", "data": client_post_uri_data}
        )
        logger.debug(f"Sent endpoint event: {client_post_uri_data}")

        async for session_message in write_stream_reader: # <-- Здесь происходит чтение сообщений для отправки
            logger.debug(f"Sending message via SSE: {session_message}")
            await sse_stream_writer.send(
                {
                    "event": "message",
                    "data": session_message.message.model_dump_json( # <-- Сообщение сериализуется в JSON
                        by_alias=True, exclude_none=True
                    ),
                }
            )
```

Здесь `session_message` — это объект `SessionMessage`, который инкапсулирует различные типы данных, включая результаты вызовов инструментов. Однако, когда результат инструмента помещается в `SessionMessage`, он уже является *полным* результатом, а не потоком.

## Вывод

Хотя FastMCP использует SSE для асинхронной связи и может передавать сообщения потоком, это не означает, что *результаты вызовов инструментов* передаются частями. Текущая архитектура `call_tool` предполагает, что инструмент завершает свою работу и возвращает полный результат, который затем инкапсулируется в сообщение и отправляется через SSE.

Для реализации потоковой передачи результатов вызовов инструментов потребовались бы значительные изменения:

1.  **Изменение сигнатуры `call_tool`:** Метод `call_tool` должен был бы возвращать асинхронный итератор или поток (например, `AsyncIterator[TextContent | ImageContent | EmbeddedResource]`), а не `Sequence`.
2.  **Изменение логики инструментов:** Сами функции инструментов должны были бы быть переписаны для генерации частичных результатов по мере их доступности (например, с использованием `yield`).
3.  **Изменение обработки на стороне сервера:** `_tool_manager.call_tool` и `_convert_to_content` должны были бы быть адаптированы для работы с потоками, а не с конечными коллекциями.
4.  **Изменение протокола SSE:** Возможно, потребовалось бы определить новый тип события SSE для потоковых результатов инструментов, чтобы клиент мог их корректно обрабатывать.

Таким образом, текущая реализация не поддерживает потоковую передачу результатов вызовов инструментов, и для этого потребовалась бы существенная переработка.
