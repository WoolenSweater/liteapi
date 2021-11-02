import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from hius.responses import PlainTextResponse
from hius.routing.exceptions import HTTPValidationError
from hius.routing.endpoint import get_http_endpoint, get_websocket_endpoint


async def http_func(request):
    return PlainTextResponse(f'Hello, world!')


async def websocket_func(websocket):
    await websocket.accept()
    await websocket.send_text(f'Hello, world!')
    await websocket.close()


async def http_func_params(request, name: str, flag: bool = False):
    return PlainTextResponse(f'Hello, {name}! Flag {flag}')


async def websocket_func_params(websocket, name: str, flag: bool = False):
    await websocket.accept()
    await websocket.send_text(f'Hello, {name}! Flag {flag}')
    await websocket.close()


class HTTPClass:

    def get(self):
        return PlainTextResponse(f'Hello, world!')


class HTTPClassParams:

    def get(self, name: str, flag: bool = False):
        return PlainTextResponse(f'Hello, {name}! Flag {flag}')


class WSClass:

    async def __call__(self):
        await self.websocket.accept()
        await self.websocket.send_text(f'Hello, world!')
        await self.websocket.close()


class WSClassParams:

    async def __call__(self, name: str, flag: bool = False):
        await self.websocket.accept()
        await self.websocket.send_text(f'Hello, {name}! Flag {flag}')
        await self.websocket.close()


# ---


_ids = ['func', 'class', 'initialized-class']

_params_http_no = (http_func, HTTPClass, HTTPClass())
_params_http_yes = (http_func_params, HTTPClassParams, HTTPClassParams())


@pytest.mark.parametrize('handler', _params_http_no, ids=_ids)
def test_http_no_params(handler):
    cli = TestClient(get_http_endpoint(handler))

    assert cli.get('/path').text == 'Hello, world!'
    assert cli.get('/path?param=test').text == 'Hello, world!'


@pytest.mark.parametrize('handler', _params_http_yes, ids=_ids)
def test_http_params_200(handler):
    cli = TestClient(get_http_endpoint(handler))

    assert cli.get('/path?name=Alice').text == 'Hello, Alice! Flag False'
    assert cli.get('/path?name=Alice&flag=1').text == 'Hello, Alice! Flag True'


@pytest.mark.parametrize('handler', _params_http_yes, ids=_ids)
def test_http_params_400(handler):
    cli = TestClient(get_http_endpoint(handler))

    with pytest.raises(HTTPValidationError):
        cli.get('/path')


# ---


_params_ws_no = (websocket_func, WSClass, WSClass())
_params_ws_yes = (websocket_func_params, WSClassParams, WSClassParams())


@pytest.mark.parametrize('handler', _params_ws_no, ids=_ids)
def test_websocket_no_params(handler):
    cli = TestClient(get_websocket_endpoint(handler))

    with cli.websocket_connect('/path') as session:
        assert session.receive_text() == 'Hello, world!'

    with cli.websocket_connect('/path?param=test') as session:
        assert session.receive_text() == 'Hello, world!'


@pytest.mark.parametrize('handler', _params_ws_yes, ids=_ids)
def test_websocket_params_200(handler):
    cli = TestClient(get_websocket_endpoint(handler))

    with cli.websocket_connect('/path?name=Alice') as session:
        assert session.receive_text() == 'Hello, Alice! Flag False'

    with cli.websocket_connect('/path?name=Alice&flag=1') as session:
        assert session.receive_text() == 'Hello, Alice! Flag True'


@pytest.mark.parametrize('handler', _params_ws_yes, ids=_ids)
def test_websocket_params_400(handler):
    cli = TestClient(get_websocket_endpoint(handler))

    with pytest.raises(WebSocketDisconnect):
        with cli.websocket_connect('/path') as session:
            session.receive_text()


# ---


def test_param_no_type():
    def handler(request, param):
        pass

    with pytest.raises(RuntimeError):
        get_http_endpoint(handler)


def test_param_arbitrary_type():
    def handler(request, param: HTTPClass = 1):
        pass

    with pytest.raises(RuntimeError):
        get_http_endpoint(handler)
