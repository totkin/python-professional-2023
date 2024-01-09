"""Набор тестов для проверки полей"""
import unittest

from nose_parameterized import parameterized

from api.fields import CharField, EmailField, PhoneField, DateField, \
    BirthDayField, GenderField, ClientIDsField, ArgumentsField
from tests.helpers import get_cases


class TestSuite(unittest.TestCase):
    """Набор тестов для проверки полей"""

    @parameterized.expand(get_cases('fields', 'char valid'))
    def test_char_field_valid(self, value, data):
        """Позитивные тесты для полей CharField"""
        field = CharField(required=data['required'],
                          nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'char invalid'))
    def test_char_field_invalid(self, value, data):
        """Негативные тесты для полей CharField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = CharField(required=data['required'],
                              nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'email valid'))
    def test_email_field_valid(self, value, data):
        """Позитивные тесты для полей EmailField"""
        field = EmailField(required=data['required'],
                           nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'email invalid'))
    def test_email_field_invalid(self, value, data):
        """Негативные тесты для полей EmailField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = EmailField(required=data['required'],
                               nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'phone valid'))
    def test_phone_field_valid(self, value, data):
        """Позитивные тесты для полей PhoneField"""
        field = PhoneField(required=data['required'],
                           nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'phone invalid'))
    def test_phone_field_invalid(self, value, data):
        """Негативные тесты для полей PhoneField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = PhoneField(required=data['required'],
                               nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'date valid'))
    def test_date_field_valid(self, value, data):
        """Позитивные тесты для полей DateField"""
        field = DateField(required=data['required'],
                          nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'date invalid'))
    def test_date_field_invalid(self, value, data):
        """Негативные тесты для полей DateField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = DateField(required=data['required'],
                              nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'birthday valid'))
    def test_birthday_field_valid(self, value, data):
        """Позитивные тесты для полей BirthDayField"""
        field = BirthDayField(required=data['required'],
                              nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'birthday invalid'))
    def test_birthday_field_invalid(self, value, data):
        """Негативные тесты для полей BirthDayField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = BirthDayField(required=data['required'],
                                  nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'gender valid'))
    def test_gender_field_valid(self, value, data):
        """Позитивные тесты для полей GenderField"""
        field = GenderField(required=data['required'],
                            nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'gender invalid'))
    def test_gender_field_invalid(self, value, data):
        """Негативные тесты для полей GenderField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = GenderField(required=data['required'],
                                nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'client_ids valid'))
    def test_client_ids_field_valid(self, value, data):
        """Позитивные тесты для полей ClientIDsField"""
        field = ClientIDsField(required=data['required'],
                               nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'client_ids invalid'))
    def test_client_ids_field_invalid(self, value, data):
        """Негативные тесты для полей ClientIDsField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = ClientIDsField(required=data['required'],
                                   nullable=data['nullable'])
            field.validate(value)

    @parameterized.expand(get_cases('fields', 'arguments valid'))
    def test_arguments_field_valid(self, value, data):
        """Позитивные тесты для полей ArgumentsField"""
        field = ArgumentsField(required=data['required'],
                               nullable=data['nullable'])
        try:
            field.validate(value)
        except Exception as exc:
            self.fail(f'Ошибка валидации поля: {exc}\n'
                      f'Поле должно быть валидным при значении равном '
                      f'"{value}" и параметрах: {data}')

    @parameterized.expand(get_cases('fields', 'arguments invalid'))
    def test_arguments_field_invalid(self, value, data):
        """Негативные тесты для полей ArgumentsField"""
        with self.assertRaises(
                ValueError,
                msg=f'Поле не может быть валидным при значении '
                    f'"{value}" и параметрах: {data}'):
            field = ArgumentsField(required=data['required'],
                                   nullable=data['nullable'])
            field.validate(value)


if __name__ == "__main__":
    unittest.main()
