import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_retrieve_course(api_client, course_factory):
    """Тест получения первого курса (retrieve-логика)."""

    course = course_factory()

    url = reverse('courses-detail', args=[course.id])

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data['id'] == course.id
    assert response_data['name'] == course.name


@pytest.mark.django_db
def test_list_courses(api_client, course_factory):
    """Тест получения списка курсов (list-логика)."""

    courses = course_factory(_quantity=3)

    url = reverse('courses-list')

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert len(response_data) == 3


@pytest.mark.django_db
def test_filter_courses_by_id(api_client, course_factory):
    """Тест фильтрации курсов по ID."""

    courses = course_factory(_quantity=3)
    target_course = courses[0]

    url = reverse('courses-list')

    response = api_client.get(url, data={'id': target_course.id})

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]['id'] == target_course.id


@pytest.mark.django_db
def test_filter_courses_by_name(api_client, course_factory):
    """Тест фильтрации курсов по названию."""
    course_factory(name='Python Basics')
    course_factory(name='Advanced Django')
    course_factory(name='Python Web Development')

    url = reverse('courses-list')

    response = api_client.get(url, data={'name': 'Python Basics'})

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]['name'] == 'Python Basics'

    response = api_client.get(url, data={'name': 'Advanced Django'})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]['name'] == 'Advanced Django'


@pytest.mark.django_db
def test_create_course(api_client):
    """Тест успешного создания курса."""
    course_data = {
        'name': 'New Course'
    }

    url = reverse('courses-list')

    response = api_client.post(url, data=course_data, format='json')

    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert response_data['name'] == course_data['name']
    assert 'id' in response_data


@pytest.mark.django_db
def test_update_course(api_client, course_factory):
    """Тест успешного обновления курса."""

    course = course_factory(name='Old Name')

    update_data = {
        'name': 'Updated Name'
    }

    url = reverse('courses-detail', args=[course.id])

    response = api_client.put(url, data=update_data, format='json')

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data['id'] == course.id
    assert response_data['name'] == update_data['name']


@pytest.mark.django_db
def test_delete_course(api_client, course_factory):
    """Тест успешного удаления курса."""

    course = course_factory()

    url = reverse('courses-detail', args=[course.id])

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    from students.models import Course
    assert not Course.objects.filter(id=course.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize('num_students, expected_status', [
    (10, status.HTTP_200_OK),  # Успех - меньше лимита
    (20, status.HTTP_200_OK),  # Успех - равно лимиту
    (21, status.HTTP_400_BAD_REQUEST),  # Ошибка - превышает лимит
])
def test_course_students_limit_on_update(
        api_client, course_factory, student_factory, settings,
        num_students, expected_status
):
    """
    Тест ограничения количества студентов при обновлении курса.
    Используем фикстуру settings для переопределения параметра.
    """

    settings.MAX_STUDENTS_PER_COURSE = 20

    course = course_factory()

    students = student_factory(_quantity=num_students + 5)

    student_ids = [student.id for student in students[:num_students]]

    update_data = {
        'name': course.name,
        'students': student_ids
    }

    url = reverse('courses-detail', args=[course.id])

    response = api_client.put(url, data=update_data, format='json')

    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        response_data = response.json()
        assert len(response_data['students']) == num_students

    elif expected_status == status.HTTP_400_BAD_REQUEST:
        response_data = response.json()
        assert 'students' in response_data or 'non_field_errors' in response_data


@pytest.mark.django_db
@pytest.mark.parametrize('num_students, expected_status', [
    (5, status.HTTP_201_CREATED),
    (20, status.HTTP_201_CREATED),
    (21, status.HTTP_400_BAD_REQUEST),
])
def test_course_students_limit_on_create(
        api_client, student_factory, settings,
        num_students, expected_status
):
    """
    Тест ограничения количества студентов при создании курса.
    """

    settings.MAX_STUDENTS_PER_COURSE = 20

    students = student_factory(_quantity=num_students)
    student_ids = [student.id for student in students]

    create_data = {
        'name': 'New Course with Students',
        'students': student_ids
    }

    url = reverse('courses-list')

    response = api_client.post(url, data=create_data, format='json')

    assert response.status_code == expected_status

    if expected_status == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data['name'] == create_data['name']
    elif expected_status == status.HTTP_400_BAD_REQUEST:
        response_data = response.json()
        assert 'students' in response_data or 'non_field_errors' in response_data


@pytest.mark.django_db
def test_partial_update_exceeding_limit(api_client, course_factory, student_factory, settings):
    """
    Тест частичного обновления с превышением лимита студентов.
    ВАЖНО: PATCH с 'students' заменяет всех студентов, а не добавляет!
    """
    settings.MAX_STUDENTS_PER_COURSE = 20

    course = course_factory()

    students = student_factory(_quantity=25)
    student_ids = [student.id for student in students]

    update_data = {
        'students': student_ids
    }

    url = reverse('courses-detail', args=[course.id])
    response = api_client.patch(url, data=update_data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert 'students' in response_data


@pytest.mark.django_db
def test_partial_update_within_limit(api_client, course_factory, student_factory, settings):
    """
    Тест частичного обновления в пределах лимита.
    """
    settings.MAX_STUDENTS_PER_COURSE = 20

    course = course_factory()

    students = student_factory(_quantity=15)
    student_ids = [student.id for student in students]

    update_data = {
        'students': student_ids
    }

    url = reverse('courses-detail', args=[course.id])
    response = api_client.patch(url, data=update_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data['students']) == 15


@pytest.mark.django_db
def test_update_replacing_students_within_limit(api_client, course_factory, student_factory, settings):
    """
    Тест замены студентов в пределах лимита.
    """
    settings.MAX_STUDENTS_PER_COURSE = 20

    course = course_factory()
    old_students = student_factory(_quantity=5)
    course.students.set(old_students)

    new_students = student_factory(_quantity=20)
    new_student_ids = [student.id for student in new_students]

    update_data = {
        'name': course.name,
        'students': new_student_ids
    }

    url = reverse('courses-detail', args=[course.id])

    response = api_client.put(url, data=update_data, format='json')

    if response.status_code != status.HTTP_200_OK:
        print(f"Ошибка: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data['students']) == 20