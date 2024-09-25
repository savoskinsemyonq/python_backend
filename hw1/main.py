import json
import math
from http import HTTPStatus
from urllib.parse import parse_qsl


async def app(scope, receive, send) -> None:
    if scope["type"] == "http" and scope["method"] == "GET":
        path = scope["path"]
        if path == "/factorial":
            await factorial(scope, send)
        elif path.startswith("/fibonacci"):
            await fibonacci(scope, send)
        elif path == "/mean":
            await mean(scope, receive, send)
        else:
            await send_error(send, status=HTTPStatus.NOT_FOUND)
    else:
        await send_error(send, status=HTTPStatus.NOT_FOUND)


async def factorial(scope, send):
    query_str = scope['query_string'].decode()
    query_params = parse_qsl(query_str)
    n_tuple = next((t for t in query_params if t[0] == 'n'), None)
    if n_tuple is None:
        return await send_error(send, status=HTTPStatus.UNPROCESSABLE_ENTITY)
    try:
        n = int(n_tuple[1])
        if n < 0:
            return await send_error(send, status=HTTPStatus.BAD_REQUEST)
        await send_response(send, HTTPStatus.OK, {"result": math.factorial(n)})
    except ValueError:
        return await send_error(send, status=HTTPStatus.UNPROCESSABLE_ENTITY)


async def fibonacci(scope, send):
    parts = scope["path"].split("/")
    try:
        n = int(parts[-1])
        if n < 0:
            return await send_error(send, status=HTTPStatus.BAD_REQUEST)
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        await send_response(send, HTTPStatus.OK, {"result": b})
    except ValueError:
        return await send_error(send, status=HTTPStatus.UNPROCESSABLE_ENTITY)


async def get_full_body(receive):
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body


async def mean(scope, receive, send):
    body = await get_full_body(receive)
    try:
        data = json.loads(body.decode())
        if not data:
            return await send_error(send, status=HTTPStatus.BAD_REQUEST)
        if not isinstance(data, list) or not all(isinstance(x, (int, float)) for x in data):
            raise ValueError
    except ValueError:
        return await send_error(send, status=HTTPStatus.UNPROCESSABLE_ENTITY)
    result = sum(data) / len(data)
    await send_response(send, HTTPStatus.OK, {"result": result})


async def send_response(send, status, response):
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [(b'content-type', b'application/json')],
    })
    await send({
        'type': 'http.response.body',
        'body': json.dumps(response).encode(),
    })


async def send_error(send, status, message=None):
    body = f'{status.value} {status.phrase}'.encode() if message is None else message
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [(b'content-type', b'text/plain')],
    })
    await send({
        'type': 'http.response.body',
        'body': body,
    })
