import pytest

import store


@pytest.fixture(scope="module", autouse=True)
def client():
    client = store.Store('localhost', 0)
    client.connect()
    yield client
    client.disconnect()


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
    val1 = client.cache_get(key)
    client.cache_set(key, value, ttl)
    val2 = client.cache_get(key)
    assert val1 is None
    assert val2 is None


@pytest.mark.parametrize('key', ['test'])
def test_persistent(client, key):
    with pytest.raises(store.StoreError):
        client.get(key)
