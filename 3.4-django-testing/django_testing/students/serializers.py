from rest_framework import serializers
from django.conf import settings
from students.models import Course


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "students")

    def validate(self, attrs):
        """
        Валидация количества студентов.
        """
        students = attrs.get('students')

        if students is not None:
            if self.instance:

                total_students = len(students)
            else:
                total_students = len(students)

            if total_students > settings.MAX_STUDENTS_PER_COURSE:
                raise serializers.ValidationError({
                    'students': [
                        f'Количество студентов на курсе не может превышать {settings.MAX_STUDENTS_PER_COURSE}'
                    ]
                })

        return attrs