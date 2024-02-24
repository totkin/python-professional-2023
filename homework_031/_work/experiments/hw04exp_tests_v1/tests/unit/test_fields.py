"""
Test specific field classes:

- fields-specific validation
- inheritance validation: that failure test cases for base field also fail for all descendants
"""


import datetime

import pytest

from api import (ArgumentsField, BaseRequest, BirthDayField, CharField,
                 ClientIDsField, DateField, EmailField, GenderField,
                 PhoneField, ValidationError)


class CasesCharField:
    cases_pass = ['', 'a', 'qwertyuiop', 'фывапролджэ', "1qaz2wsx+-*/", "\n"]
    cases_fail = [0, True, False, 123456]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = CharField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = CharField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestCharField:
    @staticmethod
    @pytest.fixture(params=CasesCharField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesCharField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert c.foo == case_pass[1].get('foo')

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesEmailField:
    cases_pass = ['@', 'guido@python.org', 'путинвв@кремль.рф']
    cases_fail = CasesCharField.cases_fail + ['', 'a', 'qwertyuiop', 'фывапролджэ', "1qaz2wsx+-*/", "\n"]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = EmailField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = EmailField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestEmailField:
    @staticmethod
    @pytest.fixture(params=CasesEmailField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesEmailField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert c.foo == case_pass[1].get('foo')

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesDateField:
    cases_pass = [
        '01.01.1970', '01.01.3000', '01.01.2000', '29.02.2004',
        (datetime.datetime.today() - datetime.timedelta(days=10)).strftime('%d.%m.%Y'),
        (datetime.datetime.today() + datetime.timedelta(days=365000)).strftime('%d.%m.%Y')
    ]
    cases_fail = [
        *CasesCharField.cases_fail,
        *['', 'a', 'qwertyuiop', 'фывапролджэ', "1qaz2wsx+-*/", "\n"],
        *['32.08.2000', '31.06.2000', '29.02.2100', '2022.01.01']
    ]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = DateField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = DateField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestDateField:
    @staticmethod
    @pytest.fixture(params=CasesDateField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesDateField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert (
            c.foo is None and case_pass[1].get('foo') is None
            or c.foo.strftime('%d.%m.%Y') == case_pass[1]['foo']
        )

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesBirthDayField:
    cases_pass = [
        (datetime.datetime.today() - datetime.timedelta(days=365 * 18)).strftime('%d.%m.%Y'),
        (datetime.datetime.today() - datetime.timedelta(days=365 * 70)).strftime('%d.%m.%Y'),
        (datetime.datetime.today() - datetime.timedelta(days=365 * 71)).strftime('%d.%m.%Y'),  # still 70yo due to leaps
    ]
    cases_fail = [
        *CasesDateField.cases_fail,
        *[
            (datetime.datetime.today() + datetime.timedelta(days=10)).strftime('%d.%m.%Y'),  # negative age
            (datetime.datetime.today() - datetime.timedelta(days=365000)).strftime('%d.%m.%Y'),  # 1000 years, too old
            (datetime.datetime.today() - datetime.timedelta(days=365 * 72)).strftime('%d.%m.%Y'),
        ]
    ]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = BirthDayField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = BirthDayField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestBirthDayField:
    @staticmethod
    @pytest.fixture(params=CasesBirthDayField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesBirthDayField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert (
            c.foo is None and case_pass[1].get('foo') is None
            or c.foo.strftime('%d.%m.%Y') == case_pass[1]['foo']
        )

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesPhoneField:
    cases_pass = [
        78005553535,
        "78005553535",
        "7FREECHEESE"  # technically, requirements do not specify that phone must be numeric
    ]
    cases_fail = [
        '',
        '7',
        '88005553535',
        'qwertyuiop0',
        False, True,
        88005553535,
        [], {}
    ]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = PhoneField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = PhoneField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestPhoneField:
    @staticmethod
    @pytest.fixture(params=CasesPhoneField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesPhoneField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert (
            c.foo is None and case_pass[1].get('foo') is None
            or c.foo == str(case_pass[1]['foo'])
        )

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesArgumentsField:
    cases_pass = [{}, {'bar': 42}, {'baz': None}, {'egg': 'ham', 'foo': 'bar'}]
    cases_fail = ['foo', [], 0, 42, 3.14, True, False, {1: 2}]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = ArgumentsField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = ArgumentsField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestArgumentsField:
    @staticmethod
    @pytest.fixture(params=CasesArgumentsField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesArgumentsField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert c.foo == (case_pass[1].get('foo') or {})

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesGenderField:
    cases_pass = [0, 1, 2]
    cases_fail = ['man', 'woman', -1, 3, 4, 5, 1.5, [], {}]

    @classmethod
    def build_params_pass(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = GenderField(required=required, nullable=nullable)

            cases_pass = [{'foo': case} for case in cls.cases_pass]
            if nullable:
                cases_pass.append({'foo': None})
            if not required:
                cases_pass.append({})

            for case in cases_pass:
                yield C, case

    @classmethod
    def build_params_fail(cls):
        for required, nullable in [(True, True), (True, False), (False, True)]:
            class C(BaseRequest):
                foo = GenderField(required=required, nullable=nullable)

            cases_fail = [{'foo': case} for case in cls.cases_fail]
            if not nullable:
                cases_fail.append({'foo': None})
            if required:
                cases_fail.append({})

            for case in cases_fail:
                yield C, case


class TestGenderField:
    @staticmethod
    @pytest.fixture(params=CasesGenderField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesGenderField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert c.foo == case_pass[1].get('foo')

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])


class CasesClientIDsField:
    cases_pass = [[0, 1, 2, 3]]
    cases_fail = [None, 0, 1, 2, {}, [], ['123']]

    @classmethod
    def build_params_pass(cls):
        class C(BaseRequest):
            foo = ClientIDsField(required=True)

        cases_pass = [{'foo': case} for case in cls.cases_pass]

        for case in cases_pass:
            yield C, case

    @classmethod
    def build_params_fail(cls):
        class C(BaseRequest):
            foo = ClientIDsField(required=True)

        cases_fail = [{'foo': case} for case in cls.cases_fail]

        for case in cases_fail:
            yield C, case


class TestClientIDsField:
    @staticmethod
    @pytest.fixture(params=CasesClientIDsField.build_params_pass())
    def case_pass(request):
        return request.param[0], request.param[1]

    @staticmethod
    @pytest.fixture(params=CasesClientIDsField.build_params_fail())
    def case_fail(request):
        return request.param[0], request.param[1]

    def test_pass(self, case_pass):
        c = case_pass[0](case_pass[1])
        assert c.foo == case_pass[1]['foo']

    def test_fail(self, case_fail):
        with pytest.raises(ValidationError):
            case_fail[0](case_fail[1])
