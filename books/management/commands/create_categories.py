from django.core.management.base import BaseCommand
from books.models import Category

class Command(BaseCommand):
    help = 'Create default categories for Bantu Books Zambia'

    def handle(self, *args, **options):
        categories = [
            {'name': 'ECZ Exam Papers', 'slug': 'ecz-papers', 'icon': 'file-alt', 
             'description': 'Past exam papers from ECZ for Grades 7, 9, and 12', 'order': 1},
            {'name': 'University Materials', 'slug': 'university', 'icon': 'university',
             'description': 'Lecture notes, past papers, and research materials from Zambian universities', 'order': 2},
            {'name': 'Zambian Novels', 'slug': 'novels', 'icon': 'book-reader',
             'description': 'Fiction and literature by Zambian authors', 'order': 3},
            {'name': 'Local Languages', 'slug': 'local-languages', 'icon': 'language',
             'description': 'Books in Bemba, Nyanja, Tonga, Lozi, and other Zambian languages', 'order': 4},
            {'name': 'Newspapers', 'slug': 'newspapers', 'icon': 'newspaper',
             'description': 'Digital archives of Zambian newspapers', 'order': 5},
            {'name': 'Religious & Culture', 'slug': 'religious', 'icon': 'church',
             'description': 'Religious texts and cultural materials', 'order': 6},
            {'name': 'Vocational Training', 'slug': 'vocational', 'icon': 'tools',
             'description': 'TEVET materials and vocational training resources', 'order': 7},
        ]

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        self.stdout.write(self.style.SUCCESS(f'Total categories: {Category.objects.count()}'))