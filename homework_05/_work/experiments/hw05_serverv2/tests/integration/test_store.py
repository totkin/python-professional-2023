"""Тесты Store"""
import unittest
from unittest.mock import patch

from api.store import Store
from tests.helpers import MockRedis


class TestSuite(unittest.TestCase):
    """Набор тестов Store"""

    @patch('redis.Redis.from_url', new=MockRedis)
    def test_get_on_mock(self):
        """Тест метода get (mock)"""
        store = Store()
        store.cache_set('index', 'true')
        result = store.get('index')
        self.assertTrue(result, 'Ошибка метода get')

    @patch('redis.Redis.from_url', new=MockRedis)
    def test_cache_get_on_mock(self):
        """Тест метода cache_get (mock)"""
        store = Store()
        store.cache_set('index', 'true')
        result = store.cache_get('index')
        self.assertTrue(result, 'Ошибка метода cache_get')

    def test_get_real(self):
        """Тест метода get (существующая БД)"""
        store = Store()
        store.cache_set('index', 'true')
        result = store.get('index')
        self.assertTrue(result, 'Ошибка метода get')

    def test_cache_get_real(self):
        """Тест метода cache_get (существующая БД)"""
        store = Store()
        store.cache_set('index', 'true')
        result = store.cache_get('index')
        self.assertTrue(result, 'Ошибка метода cache_get')


if __name__ == "__main__":
    unittest.main()
