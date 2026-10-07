"""Иерархия ошибок приложения."""


class BaseAppError(Exception):
    """Базовая ошибка приложения."""


class DataFormatError(BaseAppError):
    """Файл невозможно прочитать или его структура неверна."""


class ValidationError(BaseAppError):
    """Запись не соответствует правилам предметной области."""


class InvalidTransactionError(ValidationError):
    """Некорректная транзакция; также является ValidationError."""


class CurrencyMismatchError(InvalidTransactionError):
    """В отчёте смешаны разные валюты."""


class DuplicateIdError(InvalidTransactionError):
    """Идентификатор уже принят из другой записи."""
