import pytest
from model_bakery import baker
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Фикстура для API клиента."""
    return APIClient()


@pytest.fixture
def course_factory():
    """Фикстура для фабрики курсов."""
    def factory(**kwargs):
        return baker.make('students.Course', **kwargs)
    return factory


@pytest.fixture
def student_factory():
    """Фикстура для фабрики студентов."""
    def factory(**kwargs):
        return baker.make('students.Student', **kwargs)
    return factory