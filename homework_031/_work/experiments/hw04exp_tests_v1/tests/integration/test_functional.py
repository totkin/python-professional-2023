import datetime
import hashlib

import pytest

import api
import store


class TestRequest:
    @staticmethod
    @pytest.fixture
    def headers():
        return {}

    @staticmethod
    @pytest.fixture(scope="class")
    def store():
        client = store.Store('localhost', 6379)
        client.connect()
        client._connection_cache.flushall()
        client._connection_heavy.flushall()
        yield client
        client.disconnect()

    @staticmethod
    @pytest.fixture
    def context():
        return {}

    @staticmethod
    @pytest.fixture
    def get_valid_auth():
        def _get_valid_auth(request):
            if request.get("login") == api.ADMIN_LOGIN:
                return hashlib.sha512(
                    (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode()
                ).hexdigest()
            else:
                msg = request.get("account", "") + request.get("login", "") + api.SALT
                return hashlib.sha512(msg.encode()).hexdigest()

        return _get_valid_auth

    @staticmethod
    @pytest.fixture
    def get_response(headers, store, context, get_valid_auth):
        def _get_response(request, use_valid_auth=True):
            body = request
            if use_valid_auth:
                body['token'] = get_valid_auth(request)
            return api.method_handler({"body": body, "headers": headers}, context, store)

        return _get_response

    def test_empty_request(self, get_response):
        _, code = get_response({})
        assert code == api.INVALID_REQUEST

    @pytest.mark.parametrize('api_request', [
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, get_response, api_request):
        _, code = get_response(api_request, use_valid_auth=False)
        assert code == api.FORBIDDEN, api_request

    @pytest.mark.parametrize('api_request', [
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, get_response, api_request):
        response, code = get_response(api_request)
        assert code == api.INVALID_REQUEST, api_request
        assert len(response), response

    @pytest.mark.parametrize('api_request', [
        {"account": "horns&hoofs", 'login': 'h&f', "method": '404', "arguments": {'foo': 'bar'}},
    ])
    def test_nonexistent_method_request(self, get_response, api_request):
        response, code = get_response(api_request)
        assert code == api.NOT_FOUND, api_request
        assert len(response), response

    @pytest.mark.parametrize('arguments', [
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, get_response, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.INVALID_REQUEST, request
        assert len(response), response

    @pytest.mark.parametrize('arguments', [
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, get_response, arguments, context):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.OK, request
        score = response.get("score")
        assert isinstance(score, (int, float)), score
        assert score >= 0, score
        assert sorted(context['has']) == sorted(arguments.keys()), context

    @pytest.mark.parametrize('arguments', [
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request_caching(self, get_response, arguments, context):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.OK, request
        score = response.get("score")
        assert isinstance(score, (int, float))
        assert score >= 0
        assert sorted(context['has']) == sorted(arguments.keys()), context

        # this should change the score, but due to caching, the score should be the same
        if arguments.get('gender'):
            request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score",
                       "arguments": {**arguments, 'gender': 0}}
        else:
            request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score",
                       "arguments": {**arguments, 'gender': 1}}
        response, code = get_response(request)
        assert code == api.OK, request
        score_cached = response.get("score")
        assert score_cached == score

    def test_ok_score_admin_request(self, get_response, context):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.OK, request
        score = response.get("score")
        assert score == 42
        assert sorted(context['has']) == sorted(arguments.keys()), context

    @pytest.mark.parametrize('arguments', [
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    def test_invalid_interests_request(self, get_response, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.INVALID_REQUEST, request
        assert len(response), response

    @pytest.mark.parametrize('arguments', [
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, get_response, arguments, context):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        response, code = get_response(request)
        assert code == api.OK, request
        assert len(arguments['client_ids']) == len(response), response
        assert all(isinstance(v, list) for v in response.values()), response
        assert all(all(isinstance(t, str) for t in v) for v in response.values()), response
        assert context.get('nclients') == len(arguments['client_ids']), context
