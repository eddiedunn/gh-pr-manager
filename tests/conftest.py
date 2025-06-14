import asyncio
import inspect


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")


def pytest_pyfunc_call(pyfuncitem):
    if "asyncio" in pyfuncitem.keywords:
        func = pyfuncitem.obj
        sig = inspect.signature(func)
        kwargs = {
            name: pyfuncitem.funcargs[name]
            for name in sig.parameters
            if name in pyfuncitem.funcargs
        }
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(**kwargs))
        return True
    return None
