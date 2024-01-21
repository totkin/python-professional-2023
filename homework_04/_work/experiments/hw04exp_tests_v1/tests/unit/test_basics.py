"""
Test basic functionality for fields and requests:

- required and nullable checks for BaseField
- subclassing and request-specific validation for BaseRequest
"""


import pytest

from api import BaseField, BaseRequest, ValidationError


@pytest.fixture
def build_base_request_class():
    def _build_base_request_class(required: bool, nullable: bool):
        class C(BaseRequest):
            foo = BaseField(required=required, nullable=nullable)

        return C

    return _build_base_request_class


class TestBaseFieldNotRequiredNotNullable:
    def test_not_required_not_nullable(self, build_base_request_class):
        # optional field must be nullable, so this should fail on class creation stage
        with pytest.raises(ValueError):
            build_base_request_class(required=False, nullable=False)


class TestBaseFieldRequiredNotNullable:
    @staticmethod
    @pytest.fixture
    def RequestClass(build_base_request_class):
        return build_base_request_class(required=True, nullable=False)

    @staticmethod
    @pytest.fixture
    def ValidatedRequestClass(RequestClass):
        class C(RequestClass):
            def _validate(self):
                if not isinstance(self.foo, int):
                    raise ValidationError("foo must be int")

        return C

    @pytest.mark.parametrize("request_value", [{'foo': 'foo'}, {'foo': 0}, {'foo': 42, 'bar': None}])
    def test_base_passes(self, RequestClass, request_value):
        c = RequestClass(request_value)
        assert c.foo == request_value['foo']

    @pytest.mark.parametrize("request_value", [{}, {'foo': None}])
    def test_base_fails(self, RequestClass, request_value):
        with pytest.raises(ValidationError):
            RequestClass(request_value)

    @pytest.mark.parametrize("request_value", [{'foo': 0}, {'foo': 42, 'bar': None}])
    def test_validated_passes(self, ValidatedRequestClass, request_value):
        c = ValidatedRequestClass(request_value)
        assert c.foo == request_value['foo']

    @pytest.mark.parametrize("request_value", [{}, {'foo': None}, {'foo': 'foo'}])
    def test_validated_fails(self, ValidatedRequestClass, request_value):
        with pytest.raises(ValidationError):
            ValidatedRequestClass(request_value)


class TestBaseFieldNotRequiredNullable:
    @staticmethod
    @pytest.fixture
    def RequestClass(build_base_request_class):
        return build_base_request_class(required=False, nullable=True)

    @staticmethod
    @pytest.fixture
    def ValidatedRequestClass(RequestClass):
        class C(RequestClass):
            def _validate(self):
                if self.foo is not None and not isinstance(self.foo, int):
                    raise ValidationError("foo must be optional int")

        return C

    @pytest.mark.parametrize("request_value", [{'foo': 'foo'}, {'foo': 0}, {'foo': 42, 'bar': None}, {}, {'foo': None}])
    def test_base_passes(self, RequestClass, request_value):
        c = RequestClass(request_value)
        assert c.foo == request_value.get('foo')

    @pytest.mark.parametrize("request_value", [{}, {'foo': None}, {'foo': 0}, {'foo': 42, 'bar': None}])
    def test_validated_passes(self, ValidatedRequestClass, request_value):
        c = ValidatedRequestClass(request_value)
        assert c.foo == request_value.get('foo')

    @pytest.mark.parametrize("request_value", [{'foo': 'foo'}])
    def test_validated_fails(self, ValidatedRequestClass, request_value):
        with pytest.raises(ValidationError):
            ValidatedRequestClass(request_value)


class TestBaseFieldRequiredNullable:
    @staticmethod
    @pytest.fixture
    def RequestClass(build_base_request_class):
        return build_base_request_class(required=True, nullable=True)

    @staticmethod
    @pytest.fixture
    def ValidatedRequestClass(RequestClass):
        class C(RequestClass):
            def _validate(self):
                if self.foo is not None and not isinstance(self.foo, int):
                    raise ValidationError("foo must be optional int")

        return C

    @pytest.mark.parametrize("request_value", [{'foo': 'foo'}, {'foo': 0}, {'foo': 42, 'bar': None}, {'foo': None}])
    def test_base_passes(self, RequestClass, request_value):
        c = RequestClass(request_value)
        assert c.foo == request_value['foo']

    @pytest.mark.parametrize("request_value", [{}])
    def test_base_fails(self, RequestClass, request_value):
        with pytest.raises(ValidationError):
            RequestClass(request_value)

    @pytest.mark.parametrize("request_value", [{'foo': None}, {'foo': 0}, {'foo': 42, 'bar': None}])
    def test_validated_passes(self, ValidatedRequestClass, request_value):
        c = ValidatedRequestClass(request_value)
        assert c.foo == request_value['foo']

    @pytest.mark.parametrize("request_value", [{}, {'foo': 'foo'}])
    def test_validated_fails(self, ValidatedRequestClass, request_value):
        with pytest.raises(ValidationError):
            ValidatedRequestClass(request_value)
