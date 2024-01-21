"""
Unit tests for non-trivial request classes (the ones that are not simply lists of fields)
"""


import datetime

import pytest

from api import OnlineScoreRequest, ValidationError


class TestOnlineScoreRequest:
    @staticmethod
    @pytest.fixture(params=[
        {
            'first_name': 'John', 'last_name': 'Smith',
            'email': 'jsmith@example.com', 'phone': '77777777777',
            'gender': 1, 'birthday': (datetime.datetime.today() - datetime.timedelta(days=20*365)).strftime('%d.%m.%Y')
        },
        {
            'first_name': 'John', 'last_name': 'Smith'
        },
        {
            'first_name': 'John', 'last_name': 'Smith',
            'email': None, 'phone': None,
            'gender': None, 'birthday': None
        },
        {
            'email': 'jsmith@example.com', 'phone': '77777777777'
        },
        {
            'first_name': None, 'last_name': None,
            'email': 'jsmith@example.com', 'phone': '77777777777',
            'gender': None, 'birthday': None
        },
        {
            'gender': 1,
            'birthday': (datetime.datetime.today() - datetime.timedelta(days=20 * 365)).strftime('%d.%m.%Y')
        },
        {
            'first_name': None, 'last_name': None,
            'email': None, 'phone': None,
            'gender': 1,
            'birthday': (datetime.datetime.today() - datetime.timedelta(days=20 * 365)).strftime('%d.%m.%Y')
        },
        {
            'first_name': '', 'last_name': ''
        },
        {
            'gender': 0,
            'birthday': (datetime.datetime.today() - datetime.timedelta(days=20 * 365)).strftime('%d.%m.%Y')
        }
    ])
    def case_valid_request(request):
        return request.param

    @staticmethod
    @pytest.fixture(params=[
        {},
        {'first_name': 'John'}, {'email': 'jsmith@example.com'}, {'gender': 1},
        {'last_name': 'Smith'}, {'phone': '77777777777'},
        {'birthday': (datetime.datetime.today() - datetime.timedelta(days=20*365)).strftime('%d.%m.%Y')},
        {'first_name': 'John', 'email': 'jsmith@example.com', 'gender': 1},
        {'last_name': 'Smith', 'phone': '77777777777',
         'birthday': (datetime.datetime.today() - datetime.timedelta(days=20 * 365)).strftime('%d.%m.%Y')},
        {
            'first_name': None, 'last_name': 'Smith',
            'email': 'jsmith@example.com', 'phone': None,
            'gender': None,
            'birthday': (datetime.datetime.today() - datetime.timedelta(days=20 * 365)).strftime('%d.%m.%Y')
        },
        {
            'first_name': 'John', 'last_name': None,
            'email': None, 'phone': '77777777777',
            'gender': 1, 'birthday': None
        },
    ])
    def case_invalid_request(request):
        return request.param

    @staticmethod
    def test_valid_request(case_valid_request):
        OnlineScoreRequest(case_valid_request)

    @staticmethod
    def test_invalid_request(case_invalid_request):
        with pytest.raises(ValidationError):
            OnlineScoreRequest(case_invalid_request)
