import pytest

import store


@pytest.fixture(scope="module", autouse=True)
def client():
    client = store.Store('localhost', 6379)
    client.connect()
    client._connection_cache.flushall()
    client._connection_heavy.flushall()
    yield client
    client.disconnect()


@pytest.mark.parametrize('key', ['test_empty'])
def test_key_empty(client, key):
    val1 = client.cache_get(key)
    assert val1 is None
    val2 = client.get(key)
    assert val2 is None


@pytest.mark.parametrize('key', ['test'])
@pytest.mark.parametrize('value', [
    None,
    True, False,
    0, 1, 42, -1,
    0.0, 1234567.89, -1234567.89,
    'bar', 'baz', '',
    [], [42, -42, 1234567.89, True, False, None],
    {}, {'foo': 'bar', 'false': False, 'true': True, 'none': None, 'float': 1.5, 'int': 42, 'list': [], 'dict': {}}
])
@pytest.mark.parametrize('ttl', [60])
def test_cache(client, key, value, ttl):
    client.cache_set(key, value, ttl)
    val1 = client.cache_get(key)
    val2 = client.cache_get(key)
    assert val1 == val2 == value


@pytest.mark.parametrize('key', ['test'])
@pytest.mark.parametrize('value', [
    None,
    True, False,
    0, 1, 42, -1,
    0.0, 1234567.89, -1234567.89,
    'bar', 'baz', '',
    [], [42, -42, 1234567.89, True, False, None],
    {}, {'foo': 'bar', 'false': False, 'true': True, 'none': None, 'float': 1.5, 'int': 42, 'list': [], 'dict': {}}
])
@pytest.mark.parametrize('ttl', [60])
def test_persistent(client, key, value, ttl):
    # main difference between get and cache_get is that the latter works when server is unavailable
    # so this test works pretty much the same
    client.cache_set(key, value, ttl)
    val1 = client.get(key)
    val2 = client.get(key)
    assert val1 == val2 == value
