
from accounts.models import ResidentCategory, ResidentCategoryField


category_fields = {
    "student": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("College / Institution Name", "college-institution-name", "TEXT"),
        ("Course / Programme", "course-programme", "TEXT"),
        ("Year of Study", "year-of-study", "NUMBER"),
    ],

    "job-seeker": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Highest Qualification", "highest-qualification", "TEXT"),
        ("Preferred Job / Industry", "preferred-job-industry", "TEXT"),
        ("Preferred Job Location", "preferred-job-location", "TEXT"),
    ],

    "working-professional": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Company / Organisation Name", "company-organisation-name", "TEXT"),
        ("Designation", "designation", "TEXT"),
        ("Work Location", "work-location", "TEXT"),
    ],

    "exam-aspirant": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Exam Name", "exam-name", "TEXT"),
        ("Coaching Institute", "coaching-institute", "TEXT"),
        ("Exam Preparation Details", "exam-preparation-details", "TEXTAREA"),
    ],

    "intern": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Organisation Name", "organisation-name", "TEXT"),
        ("Training Programme", "training-programme", "TEXT"),
        ("Training Details", "training-details", "TEXTAREA"),
    ],

    "business": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Business / Company Name", "business-company-name", "TEXT"),
        ("Business Type", "business-type", "TEXT"),
        ("Work Location", "work-location", "TEXT"),
    ],

    "medical": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Hospital Name", "hospital-name", "TEXT"),
        ("Visit Purpose", "visit-purpose", "TEXT"),
    ],

    "temporary": [
        ("Purpose of Stay", "purpose-of-stay", "TEXTAREA"),
        ("Expected Duration (Days)", "expected-duration-days", "NUMBER"),
        ("Additional Details", "additional-details", "TEXTAREA"),
    ],
}


created_count = 0
existing_count = 0

for slug, fields in category_fields.items():

    category = ResidentCategory.objects.get(slug=slug)

    for order, (label, key, field_type) in enumerate(fields):

        obj, created = ResidentCategoryField.objects.get_or_create(
            category=category,
            field_key=key,
            defaults={
                "label": label,
                "field_type": field_type,
                "is_active": True,
                "display_order": order,
            }
        )

        if created:
            created_count += 1
        else:
            existing_count += 1

    print(f"Completed: {category.name}")


print("\nField creation completed!")
print("New fields:", created_count)
print("Already existing fields:", existing_count)
