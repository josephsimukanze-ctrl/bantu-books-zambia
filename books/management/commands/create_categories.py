from django.core.management.base import BaseCommand
from books.models import Category
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Create hierarchical categories for ECZ papers and educational materials with proper 3-level structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing categories before creating new ones (WARNING: This will delete all categories)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output including category tree'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Check for existing categories and offer to reset
        existing_count = Category.objects.count()
        if existing_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Found {existing_count} existing categories in the database.'))
            
            if options.get('reset'):
                if not dry_run:
                    confirm = input(self.style.WARNING('⚠️  This will delete ALL existing categories. Are you sure? (yes/no): '))
                    if confirm.lower() != 'yes':
                        self.stdout.write(self.style.WARNING('Operation cancelled.'))
                        return
                    self.stdout.write(self.style.WARNING('🗑️  Deleting all categories...'))
                    Category.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('✓ All categories deleted\n'))
                else:
                    self.stdout.write(self.style.WARNING('[DRY RUN] Would delete all categories\n'))
            elif not dry_run:
                self.stdout.write(self.style.WARNING('Run with --reset to start fresh'))
                return

        # Define the complete 3-level hierarchy
        hierarchy_structure = self.get_hierarchy_structure()
        
        if dry_run:
            self.show_dry_run_preview(hierarchy_structure)
            return
        
        # Create categories
        created_count, updated_count, errors = self.create_categories(hierarchy_structure)
        
        # Print summary
        self.print_summary(created_count, updated_count, errors)
        
        # Print category tree if verbose
        if verbose:
            self.print_category_tree()

    def get_hierarchy_structure(self):
        """Define the complete category hierarchy structure"""
        return {
            'ECZ Exam Papers': {
                'icon': 'file-alt',
                'order': 1,
                'description': 'Examination papers from the Examinations Council of Zambia',
                'subcategories': {
                    'Grade 7': {
                        'order': 1,
                        'icon': 'book',
                        'description': 'Grade 7 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Science', 'icon': 'flask', 'order': 3},
                            {'name': 'Social Studies', 'icon': 'globe', 'order': 4},
                            {'name': 'Chitonga', 'icon': 'language', 'order': 5},
                            {'name': 'Cinyanja', 'icon': 'language', 'order': 6},
                        ]
                    },
                    'Grade 9': {
                        'order': 2,
                        'icon': 'books',
                        'description': 'Grade 9 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Science', 'icon': 'flask', 'order': 3},
                            {'name': 'Social Studies', 'icon': 'globe', 'order': 4},
                            {'name': 'Design & Technology', 'icon': 'tools', 'order': 5},
                            {'name': 'Computer Studies', 'icon': 'laptop', 'order': 6},
                        ]
                    },
                    'Grade 10': {
                        'order': 3,
                        'icon': 'books',
                        'description': 'Grade 10 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Geography', 'icon': 'map-marker-alt', 'order': 6},
                            {'name': 'History', 'icon': 'history', 'order': 7},
                        ]
                    },
                    'Grade 11': {
                        'order': 4,
                        'icon': 'books',
                        'description': 'Grade 11 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Economics', 'icon': 'chart-line', 'order': 6},
                            {'name': 'Business Studies', 'icon': 'briefcase', 'order': 7},
                        ]
                    },
                    'Grade 12': {
                        'order': 5,
                        'icon': 'crown',
                        'description': 'Grade 12 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Economics', 'icon': 'chart-line', 'order': 6},
                            {'name': 'Business Studies', 'icon': 'briefcase', 'order': 7},
                            {'name': 'Geography', 'icon': 'map-marker-alt', 'order': 8},
                            {'name': 'History', 'icon': 'history', 'order': 9},
                            {'name': 'Civic Education', 'icon': 'gavel', 'order': 10},
                            {'name': 'Religious Education', 'icon': 'pray', 'order': 11},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 12},
                        ]
                    },
                }
            },
            'University Materials': {
                'icon': 'university',
                'order': 2,
                'description': 'Lecture notes, textbooks, and research materials from Zambian universities',
                'subcategories': {
                    'University of Zambia': {
                        'order': 1,
                        'icon': 'landmark',
                        'description': 'UNZA academic materials',
                        'subjects': [
                            {'name': 'Medicine', 'icon': 'stethoscope', 'order': 1},
                            {'name': 'Engineering', 'icon': 'hard-hat', 'order': 2},
                            {'name': 'Law', 'icon': 'gavel', 'order': 3},
                            {'name': 'Business', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Education', 'icon': 'chalkboard-teacher', 'order': 5},
                            {'name': 'Natural Sciences', 'icon': 'flask', 'order': 6},
                            {'name': 'Humanities', 'icon': 'book', 'order': 7},
                        ]
                    },
                    'Copperbelt University': {
                        'order': 2,
                        'icon': 'industry',
                        'description': 'CBU academic materials',
                        'subjects': [
                            {'name': 'Mining Engineering', 'icon': 'pickaxe', 'order': 1},
                            {'name': 'Mechanical Engineering', 'icon': 'cogs', 'order': 2},
                            {'name': 'Electrical Engineering', 'icon': 'bolt', 'order': 3},
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Environmental Engineering', 'icon': 'leaf', 'order': 5},
                        ]
                    },
                    'Mulungushi University': {
                        'order': 3,
                        'icon': 'university',
                        'description': 'MU academic materials',
                        'subjects': [
                            {'name': 'Commerce', 'icon': 'shopping-cart', 'order': 1},
                            {'name': 'Social Sciences', 'icon': 'users', 'order': 2},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 3},
                        ]
                    },
                }
            },
            'Zambian Novels': {
                'icon': 'book-reader',
                'order': 3,
                'description': 'Literature written by Zambian authors',
                'subcategories': {
                    'Classic Literature': {
                        'order': 1,
                        'icon': 'scroll',
                        'description': 'Classic Zambian literary works',
                        'subjects': [
                            {'name': 'Pre-Independence Literature', 'icon': 'landmark', 'order': 1},
                            {'name': 'Post-Independence Literature', 'icon': 'flag-checkered', 'order': 2},
                        ]
                    },
                    'Contemporary Fiction': {
                        'order': 2,
                        'icon': 'pen-fancy',
                        'description': 'Modern Zambian fiction',
                        'subjects': [
                            {'name': 'Zambian Drama', 'icon': 'mask', 'order': 1},
                            {'name': 'Zambian Romance', 'icon': 'heart', 'order': 2},
                            {'name': 'Zambian Adventure', 'icon': 'mountain', 'order': 3},
                            {'name': 'Zambian Historical', 'icon': 'history', 'order': 4},
                        ]
                    },
                    'Short Stories': {
                        'order': 3,
                        'icon': 'book-open',
                        'description': 'Short story collections',
                        'subjects': [
                            {'name': 'Zambian Anthologies', 'icon': 'layer-group', 'order': 1},
                            {'name': 'Zambian Biographical Stories', 'icon': 'user-circle', 'order': 2},
                        ]
                    },
                }
            },
            'Children Books': {
                'icon': 'child',
                'order': 4,
                'description': 'Educational and story books for young readers',
                'subcategories': {
                    'Early Readers (Ages 3-6)': {
                        'order': 1,
                        'icon': 'smile',
                        'description': 'Books for children ages 3-6',
                        'subjects': [
                            {'name': 'Alphabet Books', 'icon': 'a', 'order': 1, 'description': 'Learn the ABCs'},
                            {'name': 'Counting Books', 'icon': 'sort-numeric-up', 'order': 2, 'description': 'Learn numbers and counting'},
                            {'name': 'Picture Books', 'icon': 'image', 'order': 3, 'description': 'Illustrated story books'},
                        ]
                    },
                    'Middle Readers (Ages 7-10)': {
                        'order': 2,
                        'icon': 'smile-wink',
                        'description': 'Books for children ages 7-10',
                        'subjects': [
                            {'name': 'Adventure Stories', 'icon': 'mountain', 'order': 1, 'description': 'Exciting adventures'},
                            {'name': 'Science Books', 'icon': 'flask', 'order': 2, 'description': 'Educational science content'},
                            {'name': 'Cultural Stories', 'icon': 'globe-africa', 'order': 3, 'description': 'Zambian cultural stories'},
                        ]
                    },
                    'Young Adults (Ages 11-14)': {
                        'order': 3,
                        'icon': 'user-graduate',
                        'description': 'Books for young adults ages 11-14',
                        'subjects': [
                            {'name': 'YA Novels', 'icon': 'book', 'order': 1, 'description': 'Young adult fiction'},
                            {'name': 'YA Biographies', 'icon': 'user-circle', 'order': 2, 'description': 'Inspirational life stories'},
                            {'name': 'YA Educational', 'icon': 'graduation-cap', 'order': 3, 'description': 'Educational resources'},
                        ]
                    },
                }
            },
            'Professional Development': {
                'icon': 'briefcase',
                'order': 5,
                'description': 'Career and professional growth resources',
                'subcategories': {
                    'Business & Management': {
                        'order': 1,
                        'icon': 'chart-line',
                        'description': 'Business and management resources',
                        'subjects': [
                            {'name': 'Leadership', 'icon': 'crown', 'order': 1, 'description': 'Leadership skills'},
                            {'name': 'Project Management', 'icon': 'tasks', 'order': 2, 'description': 'Project management techniques'},
                            {'name': 'Marketing', 'icon': 'bullhorn', 'order': 3, 'description': 'Marketing strategies'},
                            {'name': 'Finance', 'icon': 'money-bill', 'order': 4, 'description': 'Financial management'},
                        ]
                    },
                    'Teaching Resources': {
                        'order': 2,
                        'icon': 'chalkboard-teacher',
                        'description': 'Resources for educators',
                        'subjects': [
                            {'name': 'Lesson Planning', 'icon': 'calendar-alt', 'order': 1, 'description': 'Lesson plans and templates'},
                            {'name': 'Classroom Management', 'icon': 'users', 'order': 2, 'description': 'Classroom management techniques'},
                            {'name': 'Assessment Methods', 'icon': 'check-circle', 'order': 3, 'description': 'Assessment strategies'},
                        ]
                    },
                    'Technical Skills': {
                        'order': 3,
                        'icon': 'laptop-code',
                        'description': 'Technical and digital skills',
                        'subjects': [
                            {'name': 'Programming', 'icon': 'code', 'order': 1, 'description': 'Coding and programming'},
                            {'name': 'Digital Marketing', 'icon': 'chart-line', 'order': 2, 'description': 'Digital marketing skills'},
                            {'name': 'Data Science', 'icon': 'database', 'order': 3, 'description': 'Data analysis and science'},
                        ]
                    },
                }
            },
        }
    def get_hierarchy_structure(self):
        """Define the complete category hierarchy structure"""
        return {
            'ECZ Exam Papers': {
                'icon': 'file-alt',
                'order': 1,
                'description': 'Examination papers from the Examinations Council of Zambia',
                'subcategories': {
                    'Grade 7': {
                        'order': 1,
                        'icon': 'book',
                        'description': 'Grade 7 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Science', 'icon': 'flask', 'order': 3},
                            {'name': 'Social Studies', 'icon': 'globe', 'order': 4},
                            {'name': 'Chitonga', 'icon': 'language', 'order': 5},
                            {'name': 'Cinyanja', 'icon': 'language', 'order': 6},
                        ]
                    },
                    'Grade 9': {
                        'order': 2,
                        'icon': 'books',
                        'description': 'Grade 9 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Science', 'icon': 'flask', 'order': 3},
                            {'name': 'Social Studies', 'icon': 'globe', 'order': 4},
                            {'name': 'Design & Technology', 'icon': 'tools', 'order': 5},
                            {'name': 'Computer Studies', 'icon': 'laptop', 'order': 6},
                        ]
                    },
                    'Grade 10': {
                        'order': 3,
                        'icon': 'books',
                        'description': 'Grade 10 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Geography', 'icon': 'map-marker-alt', 'order': 6},
                            {'name': 'History', 'icon': 'history', 'order': 7},
                        ]
                    },
                    'Grade 11': {
                        'order': 4,
                        'icon': 'books',
                        'description': 'Grade 11 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Economics', 'icon': 'chart-line', 'order': 6},
                            {'name': 'Business Studies', 'icon': 'briefcase', 'order': 7},
                        ]
                    },
                    'Grade 12': {
                        'order': 5,
                        'icon': 'crown',
                        'description': 'Grade 12 Examination Papers',
                        'subjects': [
                            {'name': 'English', 'icon': 'book', 'order': 1},
                            {'name': 'Mathematics', 'icon': 'calculator', 'order': 2},
                            {'name': 'Biology', 'icon': 'dna', 'order': 3},
                            {'name': 'Chemistry', 'icon': 'flask', 'order': 4},
                            {'name': 'Physics', 'icon': 'atom', 'order': 5},
                            {'name': 'Economics', 'icon': 'chart-line', 'order': 6},
                            {'name': 'Business Studies', 'icon': 'briefcase', 'order': 7},
                            {'name': 'Geography', 'icon': 'map-marker-alt', 'order': 8},
                            {'name': 'History', 'icon': 'history', 'order': 9},
                            {'name': 'Civic Education', 'icon': 'gavel', 'order': 10},
                            {'name': 'Religious Education', 'icon': 'pray', 'order': 11},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 12},
                        ]
                    },
                }
            },
            'College Materials': {  # NEW CATEGORY
                'icon': 'university',
                'order': 2,
                'description': 'College and tertiary education resources, notes, and textbooks',
                'subcategories': {
                    'Certificate Programs': {
                        'order': 1,
                        'icon': 'certificate',
                        'description': 'Certificate level course materials',
                        'subjects': [
                            {'name': 'Business Studies', 'icon': 'chart-line', 'order': 1, 'description': 'Business certificate materials'},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 2, 'description': 'IT certificate materials'},
                            {'name': 'Accounting', 'icon': 'calculator', 'order': 3, 'description': 'Accounting certificate materials'},
                            {'name': 'Secretarial Studies', 'icon': 'file-alt', 'order': 4, 'description': 'Secretarial studies materials'},
                            {'name': 'Teaching Methodology', 'icon': 'chalkboard-teacher', 'order': 5, 'description': 'Teaching certificate materials'},
                        ]
                    },
                    'Diploma Programs': {
                        'order': 2,
                        'icon': 'diploma',
                        'description': 'Diploma level course materials',
                        'subjects': [
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 1, 'description': 'Business diploma materials'},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 2, 'description': 'Computer science diploma'},
                            {'name': 'Accounting', 'icon': 'calculator', 'order': 3, 'description': 'Accounting diploma materials'},
                            {'name': 'Marketing', 'icon': 'bullhorn', 'order': 4, 'description': 'Marketing diploma materials'},
                            {'name': 'Human Resources', 'icon': 'users', 'order': 5, 'description': 'HR diploma materials'},
                            {'name': 'Journalism', 'icon': 'newspaper', 'order': 6, 'description': 'Journalism diploma materials'},
                            {'name': 'Public Health', 'icon': 'heartbeat', 'order': 7, 'description': 'Public health diploma'},
                        ]
                    },
                    'Teaching Colleges': {
                        'order': 3,
                        'icon': 'chalkboard-teacher',
                        'description': 'Teaching college materials and resources',
                        'subjects': [
                            {'name': 'Primary Education', 'icon': 'book', 'order': 1, 'description': 'Primary teaching materials'},
                            {'name': 'Secondary Education', 'icon': 'books', 'order': 2, 'description': 'Secondary teaching materials'},
                            {'name': 'Special Education', 'icon': 'hand-holding-heart', 'order': 3, 'description': 'Special needs education'},
                            {'name': 'Early Childhood Education', 'icon': 'child', 'order': 4, 'description': 'ECE materials'},
                            {'name': 'Educational Psychology', 'icon': 'brain', 'order': 5, 'description': 'Educational psychology'},
                        ]
                    },
                    'Technical Colleges': {
                        'order': 4,
                        'icon': 'tools',
                        'description': 'Technical and vocational college materials',
                        'subjects': [
                            {'name': 'Electrical Engineering', 'icon': 'bolt', 'order': 1, 'description': 'Electrical engineering'},
                            {'name': 'Mechanical Engineering', 'icon': 'cogs', 'order': 2, 'description': 'Mechanical engineering'},
                            {'name': 'Civil Engineering', 'icon': 'building', 'order': 3, 'description': 'Civil engineering'},
                            {'name': 'Automotive Engineering', 'icon': 'car', 'order': 4, 'description': 'Automotive engineering'},
                            {'name': 'Plumbing', 'icon': 'faucet', 'order': 5, 'description': 'Plumbing materials'},
                            {'name': 'Carpentry', 'icon': 'hammer', 'order': 6, 'description': 'Carpentry materials'},
                            {'name': 'Welding', 'icon': 'fire', 'order': 7, 'description': 'Welding materials'},
                        ]
                    },
                    'Nursing Colleges': {
                        'order': 5,
                        'icon': 'heartbeat',
                        'description': 'Nursing and healthcare college materials',
                        'subjects': [
                            {'name': 'General Nursing', 'icon': 'stethoscope', 'order': 1, 'description': 'General nursing materials'},
                            {'name': 'Midwifery', 'icon': 'baby', 'order': 2, 'description': 'Midwifery materials'},
                            {'name': 'Public Health Nursing', 'icon': 'hospital', 'order': 3, 'description': 'Public health nursing'},
                            {'name': 'Mental Health Nursing', 'icon': 'brain', 'order': 4, 'description': 'Mental health nursing'},
                            {'name': 'Pediatric Nursing', 'icon': 'child', 'order': 5, 'description': 'Pediatric nursing'},
                            {'name': 'Clinical Medicine', 'icon': 'clinic-medical', 'order': 6, 'description': 'Clinical medicine'},
                            {'name': 'Pharmacy', 'icon': 'prescription-bottle', 'order': 7, 'description': 'Pharmacy materials'},
                        ]
                    },
                }
            },
            'University Materials': {
                'icon': 'university',
                'order': 3,
                'description': 'Lecture notes, textbooks, and research materials from Zambian universities',
                'subcategories': {
                    'University of Zambia': {
                        'order': 1,
                        'icon': 'landmark',
                        'description': 'UNZA academic materials',
                        'subjects': [
                            {'name': 'Medicine', 'icon': 'stethoscope', 'order': 1},
                            {'name': 'Engineering', 'icon': 'hard-hat', 'order': 2},
                            {'name': 'Law', 'icon': 'gavel', 'order': 3},
                            {'name': 'Business', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Education', 'icon': 'chalkboard-teacher', 'order': 5},
                            {'name': 'Natural Sciences', 'icon': 'flask', 'order': 6},
                            {'name': 'Humanities', 'icon': 'book', 'order': 7},
                        ]
                    },
                    'Copperbelt University': {
                        'order': 2,
                        'icon': 'industry',
                        'description': 'CBU academic materials',
                        'subjects': [
                            {'name': 'Mining Engineering', 'icon': 'pickaxe', 'order': 1},
                            {'name': 'Mechanical Engineering', 'icon': 'cogs', 'order': 2},
                            {'name': 'Electrical Engineering', 'icon': 'bolt', 'order': 3},
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Environmental Engineering', 'icon': 'leaf', 'order': 5},
                        ]
                    },
                    'Mulungushi University': {
                        'order': 3,
                        'icon': 'university',
                        'description': 'MU academic materials',
                        'subjects': [
                            {'name': 'Commerce', 'icon': 'shopping-cart', 'order': 1},
                            {'name': 'Social Sciences', 'icon': 'users', 'order': 2},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 3},
                        ]
                    },
                }
            },
            'Zambian Novels': {
                'icon': 'book-reader',
                'order': 4,
                'description': 'Literature written by Zambian authors',
                'subcategories': {
                    'Classic Literature': {
                        'order': 1,
                        'icon': 'scroll',
                        'description': 'Classic Zambian literary works',
                        'subjects': [
                            {'name': 'Pre-Independence Literature', 'icon': 'landmark', 'order': 1},
                            {'name': 'Post-Independence Literature', 'icon': 'flag-checkered', 'order': 2},
                        ]
                    },
                    'Contemporary Fiction': {
                        'order': 2,
                        'icon': 'pen-fancy',
                        'description': 'Modern Zambian fiction',
                        'subjects': [
                            {'name': 'Zambian Drama', 'icon': 'mask', 'order': 1},
                            {'name': 'Zambian Romance', 'icon': 'heart', 'order': 2},
                            {'name': 'Zambian Adventure', 'icon': 'mountain', 'order': 3},
                            {'name': 'Zambian Historical', 'icon': 'history', 'order': 4},
                        ]
                    },
                    'Short Stories': {
                        'order': 3,
                        'icon': 'book-open',
                        'description': 'Short story collections',
                        'subjects': [
                            {'name': 'Zambian Anthologies', 'icon': 'layer-group', 'order': 1},
                            {'name': 'Zambian Biographical Stories', 'icon': 'user-circle', 'order': 2},
                        ]
                    },
                }
            },
            'Children Books': {
                'icon': 'child',
                'order': 5,
                'description': 'Educational and story books for young readers',
                'subcategories': {
                    'Early Readers (Ages 3-6)': {
                        'order': 1,
                        'icon': 'smile',
                        'description': 'Books for children ages 3-6',
                        'subjects': [
                            {'name': 'Alphabet Books', 'icon': 'a', 'order': 1, 'description': 'Learn the ABCs'},
                            {'name': 'Counting Books', 'icon': 'sort-numeric-up', 'order': 2, 'description': 'Learn numbers and counting'},
                            {'name': 'Picture Books', 'icon': 'image', 'order': 3, 'description': 'Illustrated story books'},
                        ]
                    },
                    'Middle Readers (Ages 7-10)': {
                        'order': 2,
                        'icon': 'smile-wink',
                        'description': 'Books for children ages 7-10',
                        'subjects': [
                            {'name': 'Adventure Stories', 'icon': 'mountain', 'order': 1, 'description': 'Exciting adventures'},
                            {'name': 'Science Books', 'icon': 'flask', 'order': 2, 'description': 'Educational science content'},
                            {'name': 'Cultural Stories', 'icon': 'globe-africa', 'order': 3, 'description': 'Zambian cultural stories'},
                        ]
                    },
                    'Young Adults (Ages 11-14)': {
                        'order': 3,
                        'icon': 'user-graduate',
                        'description': 'Books for young adults ages 11-14',
                        'subjects': [
                            {'name': 'YA Novels', 'icon': 'book', 'order': 1, 'description': 'Young adult fiction'},
                            {'name': 'YA Biographies', 'icon': 'user-circle', 'order': 2, 'description': 'Inspirational life stories'},
                            {'name': 'YA Educational', 'icon': 'graduation-cap', 'order': 3, 'description': 'Educational resources'},
                        ]
                    },
                }
            },
            'Professional Development': {
                'icon': 'briefcase',
                'order': 6,
                'description': 'Career and professional growth resources',
                'subcategories': {
                    'Business & Management': {
                        'order': 1,
                        'icon': 'chart-line',
                        'description': 'Business and management resources',
                        'subjects': [
                            {'name': 'Leadership', 'icon': 'crown', 'order': 1, 'description': 'Leadership skills'},
                            {'name': 'Project Management', 'icon': 'tasks', 'order': 2, 'description': 'Project management techniques'},
                            {'name': 'Marketing', 'icon': 'bullhorn', 'order': 3, 'description': 'Marketing strategies'},
                            {'name': 'Finance', 'icon': 'money-bill', 'order': 4, 'description': 'Financial management'},
                        ]
                    },
                    'Teaching Resources': {
                        'order': 2,
                        'icon': 'chalkboard-teacher',
                        'description': 'Resources for educators',
                        'subjects': [
                            {'name': 'Lesson Planning', 'icon': 'calendar-alt', 'order': 1, 'description': 'Lesson plans and templates'},
                            {'name': 'Classroom Management', 'icon': 'users', 'order': 2, 'description': 'Classroom management techniques'},
                            {'name': 'Assessment Methods', 'icon': 'check-circle', 'order': 3, 'description': 'Assessment strategies'},
                        ]
                    },
                    'Technical Skills': {
                        'order': 3,
                        'icon': 'laptop-code',
                        'description': 'Technical and digital skills',
                        'subjects': [
                            {'name': 'Programming', 'icon': 'code', 'order': 1, 'description': 'Coding and programming'},
                            {'name': 'Digital Marketing', 'icon': 'chart-line', 'order': 2, 'description': 'Digital marketing skills'},
                            {'name': 'Data Science', 'icon': 'database', 'order': 3, 'description': 'Data analysis and science'},
                        ]
                    },
                }
            },
        }
    def create_categories(self, hierarchy_structure):
        """Create categories from hierarchy structure"""
        created_count = 0
        updated_count = 0
        errors = []
        
        for parent_name, parent_data in hierarchy_structure.items():
            parent_slug = slugify(parent_name)
            
            # Create parent (Level 0)
            parent, created = Category.objects.get_or_create(
                slug=parent_slug,
                defaults={
                    'name': parent_name,
                    'icon': parent_data['icon'],
                    'order': parent_data['order'],
                    'description': parent_data.get('description', ''),
                    'is_active': True,
                    'level': 0,
                    'parent': None
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'📁 Created parent: {parent.name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.INFO(f'📁 Parent exists: {parent.name}'))
                # Update existing parent if needed
                updated = False
                if parent.icon != parent_data['icon']:
                    parent.icon = parent_data['icon']
                    updated = True
                if parent.order != parent_data['order']:
                    parent.order = parent_data['order']
                    updated = True
                if updated:
                    parent.save()
                    updated_count += 1
                    self.stdout.write(self.style.INFO(f'   Updated: {parent.name}'))
            
            # Create Level 1: Subcategories
            for sub_name, sub_data in parent_data.get('subcategories', {}).items():
                # Create full name with parent context for uniqueness
                full_sub_name = f"{parent_name} - {sub_name}"
                sub_slug = slugify(full_sub_name)
                
                sub_category, sub_created = Category.objects.get_or_create(
                    slug=sub_slug,
                    defaults={
                        'name': full_sub_name,
                        'icon': sub_data.get('icon', parent_data.get('icon', 'folder')),
                        'parent': parent,
                        'order': sub_data.get('order', 999),
                        'description': sub_data.get('description', f'{sub_name} resources for {parent_name}'),
                        'is_active': True,
                        'level': 1
                    }
                )
                
                if sub_created:
                    self.stdout.write(self.style.SUCCESS(f'  📂 Created: {sub_category.name}'))
                    created_count += 1
                else:
                    self.stdout.write(self.style.INFO(f'  📂 Subcategory exists: {sub_category.name}'))
                
                # Create Level 2: Subjects/Courses
                for subject in sub_data.get('subjects', []):
                    # Create full name with full path for uniqueness
                    full_subject_name = f"{parent_name} - {sub_name} - {subject['name']}"
                    subject_slug = slugify(full_subject_name)
                    
                    try:
                        subject_category, subject_created = Category.objects.get_or_create(
                            slug=subject_slug,
                            defaults={
                                'name': full_subject_name,
                                'icon': subject.get('icon', 'book'),
                                'parent': sub_category,
                                'order': subject.get('order', 999),
                                'description': subject.get('description', f'{subject["name"]} - {sub_name} level'),
                                'is_active': True,
                                'level': 2
                            }
                        )
                        
                        if subject_created:
                            self.stdout.write(self.style.SUCCESS(f'    📄 Created: {subject_category.name}'))
                            created_count += 1
                        else:
                            self.stdout.write(self.style.INFO(f'    📄 Subject exists: {subject_category.name}'))
                    except IntegrityError as e:
                        error_msg = f'Error creating subject "{subject["name"]}" under "{sub_name}": {str(e)}'
                        self.stdout.write(self.style.ERROR(f'    ❌ {error_msg}'))
                        errors.append(error_msg)
        
        return created_count, updated_count, errors

    def show_dry_run_preview(self, hierarchy_structure):
        """Show preview of what would be created"""
        for parent_name, parent_data in hierarchy_structure.items():
            self.stdout.write(self.style.WARNING(f'\n📁 Would create parent: {parent_name}'))
            for sub_name, sub_data in parent_data.get('subcategories', {}).items():
                self.stdout.write(self.style.WARNING(f'  📂 Would create: {parent_name} - {sub_name}'))
                subjects = sub_data.get('subjects', [])
                for subject in subjects:
                    full_name = f"{parent_name} - {sub_name} - {subject['name']}"
                    self.stdout.write(self.style.WARNING(f'    📄 Would create: {full_name}'))
        
        self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were made. Run without --dry-run to apply changes.'))

    def print_summary(self, created_count, updated_count, errors):
        """Print summary of category creation"""
        self.stdout.write(self.style.SUCCESS(f'\n✅ Hierarchical categories created/updated successfully!'))
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Updated: {updated_count}')
        
        # Print statistics
        total_categories = Category.objects.filter(is_active=True).count()
        level_0_count = Category.objects.filter(level=0, is_active=True).count()
        level_1_count = Category.objects.filter(level=1, is_active=True).count()
        level_2_count = Category.objects.filter(level=2, is_active=True).count()
        
        self.stdout.write(f'\n📊 Category Statistics:')
        self.stdout.write(f'   Total categories: {total_categories}')
        self.stdout.write(f'   📁 Top Level (Level 0): {level_0_count}')
        self.stdout.write(f'   📂 Subcategories (Level 1): {level_1_count}')
        self.stdout.write(f'   📄 Subjects/Courses (Level 2): {level_2_count}')
        
        if errors:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Encountered {len(errors)} errors:'))
            for error in errors[:5]:
                self.stdout.write(self.style.WARNING(f'   • {error}'))

    def print_category_tree(self):
        """Print the complete category tree"""
        self.stdout.write('\n🌳 Complete Category Tree:')
        top_categories = Category.objects.filter(parent__isnull=True, is_active=True).order_by('order')
        
        def print_tree(category, prefix="", is_last=True):
            # Choose emoji based on level
            if category.level == 0:
                emoji = "📁"
            elif category.level == 1:
                emoji = "📂"
            else:
                emoji = "📄"
            
            connector = "└── " if is_last else "├── "
            # Show book count if available
            book_count = category.books.count()
            book_info = f" ({book_count} books)" if book_count > 0 else ""
            self.stdout.write(f'{prefix}{connector}{emoji} {category.name}{book_info}')
            
            children = category.subcategories.filter(is_active=True).order_by('order')
            for i, child in enumerate(children):
                is_child_last = i == len(children) - 1
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(child, new_prefix, is_child_last)
        
        for i, cat in enumerate(top_categories):
            is_last = i == len(top_categories) - 1
            print_tree(cat, "", is_last)