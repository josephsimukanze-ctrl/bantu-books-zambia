from django.core.management.base import BaseCommand
from books.models import Category
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Add College, University Materials, and Zambian Newspapers categories'

    def add_arguments(self, parser):
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
        
        # Define the hierarchy
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
        """Define the complete category hierarchy structure - COLLEGE, UNIVERSITY, AND NEWSPAPERS"""
        return {
            'College Materials': {
                'icon': 'university',
                'order': 1,
                'description': 'College and tertiary education resources, notes, and textbooks',
                'subcategories': {
                    'Certificate Programs': {
                        'order': 1,
                        'icon': 'certificate',
                        'description': 'Certificate level course materials',
                        'subjects': [
                            {'name': 'Business Studies', 'icon': 'chart-line', 'order': 1},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 2},
                            {'name': 'Accounting', 'icon': 'calculator', 'order': 3},
                            {'name': 'Secretarial Studies', 'icon': 'file-alt', 'order': 4},
                            {'name': 'Teaching Methodology', 'icon': 'chalkboard-teacher', 'order': 5},
                        ]
                    },
                    'Diploma Programs': {
                        'order': 2,
                        'icon': 'diploma',
                        'description': 'Diploma level course materials',
                        'subjects': [
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 1},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 2},
                            {'name': 'Accounting', 'icon': 'calculator', 'order': 3},
                            {'name': 'Marketing', 'icon': 'bullhorn', 'order': 4},
                            {'name': 'Human Resources', 'icon': 'users', 'order': 5},
                            {'name': 'Journalism', 'icon': 'newspaper', 'order': 6},
                            {'name': 'Public Health', 'icon': 'heartbeat', 'order': 7},
                        ]
                    },
                    'Teaching Colleges': {
                        'order': 3,
                        'icon': 'chalkboard-teacher',
                        'description': 'Teaching college materials and resources',
                        'subjects': [
                            {'name': 'Primary Education', 'icon': 'book', 'order': 1},
                            {'name': 'Secondary Education', 'icon': 'books', 'order': 2},
                            {'name': 'Special Education', 'icon': 'hand-holding-heart', 'order': 3},
                            {'name': 'Early Childhood Education', 'icon': 'child', 'order': 4},
                            {'name': 'Educational Psychology', 'icon': 'brain', 'order': 5},
                        ]
                    },
                    'Technical Colleges': {
                        'order': 4,
                        'icon': 'tools',
                        'description': 'Technical and vocational college materials',
                        'subjects': [
                            {'name': 'Electrical Engineering', 'icon': 'bolt', 'order': 1},
                            {'name': 'Mechanical Engineering', 'icon': 'cogs', 'order': 2},
                            {'name': 'Civil Engineering', 'icon': 'building', 'order': 3},
                            {'name': 'Automotive Engineering', 'icon': 'car', 'order': 4},
                            {'name': 'Plumbing', 'icon': 'faucet', 'order': 5},
                            {'name': 'Carpentry', 'icon': 'hammer', 'order': 6},
                            {'name': 'Welding', 'icon': 'fire', 'order': 7},
                        ]
                    },
                    'Nursing Colleges': {
                        'order': 5,
                        'icon': 'heartbeat',
                        'description': 'Nursing and healthcare college materials',
                        'subjects': [
                            {'name': 'General Nursing', 'icon': 'stethoscope', 'order': 1},
                            {'name': 'Midwifery', 'icon': 'baby', 'order': 2},
                            {'name': 'Public Health Nursing', 'icon': 'hospital', 'order': 3},
                            {'name': 'Mental Health Nursing', 'icon': 'brain', 'order': 4},
                            {'name': 'Pediatric Nursing', 'icon': 'child', 'order': 5},
                            {'name': 'Clinical Medicine', 'icon': 'clinic-medical', 'order': 6},
                            {'name': 'Pharmacy', 'icon': 'prescription-bottle', 'order': 7},
                        ]
                    },
                }
            },
            'University Materials': {
                'icon': 'university',
                'order': 2,
                'description': 'University level lecture notes, textbooks, and research materials',
                'subcategories': {
                    'University of Zambia (UNZA)': {
                        'order': 1,
                        'icon': 'landmark',
                        'description': 'Academic materials from the University of Zambia',
                        'subjects': [
                            {'name': 'Medicine', 'icon': 'stethoscope', 'order': 1},
                            {'name': 'Engineering', 'icon': 'hard-hat', 'order': 2},
                            {'name': 'Law', 'icon': 'gavel', 'order': 3},
                            {'name': 'Business', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Education', 'icon': 'chalkboard-teacher', 'order': 5},
                            {'name': 'Natural Sciences', 'icon': 'flask', 'order': 6},
                            {'name': 'Humanities', 'icon': 'book', 'order': 7},
                            {'name': 'Social Sciences', 'icon': 'users', 'order': 8},
                            {'name': 'Agriculture', 'icon': 'leaf', 'order': 9},
                            {'name': 'Veterinary Medicine', 'icon': 'paw', 'order': 10},
                        ]
                    },
                    'Copperbelt University (CBU)': {
                        'order': 2,
                        'icon': 'industry',
                        'description': 'Academic materials from Copperbelt University',
                        'subjects': [
                            {'name': 'Mining Engineering', 'icon': 'pickaxe', 'order': 1},
                            {'name': 'Mechanical Engineering', 'icon': 'cogs', 'order': 2},
                            {'name': 'Electrical Engineering', 'icon': 'bolt', 'order': 3},
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Environmental Engineering', 'icon': 'leaf', 'order': 5},
                            {'name': 'Chemical Engineering', 'icon': 'flask', 'order': 6},
                            {'name': 'Civil Engineering', 'icon': 'building', 'order': 7},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 8},
                        ]
                    },
                    'Mulungushi University': {
                        'order': 3,
                        'icon': 'university',
                        'description': 'Academic materials from Mulungushi University',
                        'subjects': [
                            {'name': 'Commerce', 'icon': 'shopping-cart', 'order': 1},
                            {'name': 'Social Sciences', 'icon': 'users', 'order': 2},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 3},
                            {'name': 'Economics', 'icon': 'chart-line', 'order': 4},
                            {'name': 'Development Studies', 'icon': 'globe', 'order': 5},
                        ]
                    },
                    'Kwame Nkrumah University': {
                        'order': 4,
                        'icon': 'university',
                        'description': 'Academic materials from Kwame Nkrumah University',
                        'subjects': [
                            {'name': 'Agricultural Sciences', 'icon': 'leaf', 'order': 1},
                            {'name': 'Natural Resources', 'icon': 'mountain', 'order': 2},
                            {'name': 'Environmental Sciences', 'icon': 'globe', 'order': 3},
                            {'name': 'Food Science', 'icon': 'apple-alt', 'order': 4},
                        ]
                    },
                    'Chalimbana University': {
                        'order': 5,
                        'icon': 'university',
                        'description': 'Academic materials from Chalimbana University',
                        'subjects': [
                            {'name': 'Education', 'icon': 'chalkboard-teacher', 'order': 1},
                            {'name': 'Special Education', 'icon': 'hand-holding-heart', 'order': 2},
                            {'name': 'Educational Psychology', 'icon': 'brain', 'order': 3},
                            {'name': 'Curriculum Studies', 'icon': 'book', 'order': 4},
                        ]
                    },
                    'Lusaka Apex Medical University': {
                        'order': 6,
                        'icon': 'hospital',
                        'description': 'Medical and health sciences materials',
                        'subjects': [
                            {'name': 'Medicine', 'icon': 'stethoscope', 'order': 1},
                            {'name': 'Pharmacy', 'icon': 'prescription-bottle', 'order': 2},
                            {'name': 'Nursing', 'icon': 'heartbeat', 'order': 3},
                            {'name': 'Public Health', 'icon': 'hospital', 'order': 4},
                            {'name': 'Biomedical Sciences', 'icon': 'dna', 'order': 5},
                        ]
                    },
                    'DMI St. Eugene University': {
                        'order': 7,
                        'icon': 'university',
                        'description': 'Academic materials from DMI St. Eugene University',
                        'subjects': [
                            {'name': 'Business Management', 'icon': 'chart-line', 'order': 1},
                            {'name': 'Information Technology', 'icon': 'laptop-code', 'order': 2},
                            {'name': 'Theology', 'icon': 'pray', 'order': 3},
                            {'name': 'Humanities', 'icon': 'book', 'order': 4},
                        ]
                    },
                    'Northrise University': {
                        'order': 8,
                        'icon': 'university',
                        'description': 'Academic materials from Northrise University',
                        'subjects': [
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 1},
                            {'name': 'Computer Science', 'icon': 'laptop-code', 'order': 2},
                            {'name': 'Theology', 'icon': 'pray', 'order': 3},
                            {'name': 'Education', 'icon': 'chalkboard-teacher', 'order': 4},
                        ]
                    },
                    'ZCAS University': {
                        'order': 9,
                        'icon': 'university',
                        'description': 'Academic materials from ZCAS University',
                        'subjects': [
                            {'name': 'Accounting', 'icon': 'calculator', 'order': 1},
                            {'name': 'Finance', 'icon': 'money-bill', 'order': 2},
                            {'name': 'Business Administration', 'icon': 'chart-line', 'order': 3},
                            {'name': 'Information Systems', 'icon': 'laptop-code', 'order': 4},
                        ]
                    },
                    'Victoria Falls University': {
                        'order': 10,
                        'icon': 'water',
                        'description': 'Academic materials from Victoria Falls University',
                        'subjects': [
                            {'name': 'Tourism Management', 'icon': 'umbrella-beach', 'order': 1},
                            {'name': 'Hospitality Management', 'icon': 'hotel', 'order': 2},
                            {'name': 'Business Management', 'icon': 'chart-line', 'order': 3},
                        ]
                    },
                }
            },
            'Zambian Newspapers': {
                'icon': 'newspaper',
                'order': 3,
                'description': 'Digital archives of Zambian newspapers and publications',
                'subcategories': {
                    'Daily Newspapers': {
                        'order': 1,
                        'icon': 'newspaper',
                        'description': 'Daily Zambian newspapers',
                        'subjects': [
                            {'name': 'Zambia Daily Mail', 'icon': 'newspaper', 'order': 1},
                            {'name': 'Times of Zambia', 'icon': 'newspaper', 'order': 2},
                            {'name': 'The Mast', 'icon': 'newspaper', 'order': 3},
                            {'name': 'Daily Nation Zambia', 'icon': 'newspaper', 'order': 4},
                        ]
                    },
                    'Weekly Newspapers': {
                        'order': 2,
                        'icon': 'calendar-week',
                        'description': 'Weekly Zambian newspapers',
                        'subjects': [
                            {'name': 'Zambia Daily Mail Weekend Edition', 'icon': 'newspaper', 'order': 1},
                            {'name': 'Times of Zambia Weekend', 'icon': 'newspaper', 'order': 2},
                            {'name': 'The Weekend Post', 'icon': 'newspaper', 'order': 3},
                            {'name': 'Sunday Times of Zambia', 'icon': 'newspaper', 'order': 4},
                        ]
                    },
                    'Sunday Newspapers': {
                        'order': 3,
                        'icon': 'calendar-day',
                        'description': 'Sunday edition Zambian newspapers',
                        'subjects': [
                            {'name': 'Sunday Mail', 'icon': 'newspaper', 'order': 1},
                            {'name': 'Sunday Times', 'icon': 'newspaper', 'order': 2},
                            {'name': 'Sunday Post', 'icon': 'newspaper', 'order': 3},
                        ]
                    },
                    'Community Newspapers': {
                        'order': 4,
                        'icon': 'users',
                        'description': 'Local community newspapers',
                        'subjects': [
                            {'name': 'Luanshya Times', 'icon': 'newspaper', 'order': 1},
                            {'name': 'Kitwe Times', 'icon': 'newspaper', 'order': 2},
                            {'name': 'Ndola Post', 'icon': 'newspaper', 'order': 3},
                            {'name': 'Livingstone Sun', 'icon': 'sun', 'order': 4},
                            {'name': 'Chipata Journal', 'icon': 'newspaper', 'order': 5},
                            {'name': 'Kasama Observer', 'icon': 'newspaper', 'order': 6},
                            {'name': 'Solwezi Star', 'icon': 'star', 'order': 7},
                        ]
                    },
                    'Digital News Platforms': {
                        'order': 5,
                        'icon': 'laptop',
                        'description': 'Online Zambian news platforms',
                        'subjects': [
                            {'name': 'Lusaka Times', 'icon': 'globe', 'order': 1},
                            {'name': 'Zambia Reports', 'icon': 'globe', 'order': 2},
                            {'name': 'News Diggers', 'icon': 'globe', 'order': 3},
                            {'name': 'Zambia Watchdog', 'icon': 'globe', 'order': 4},
                            {'name': 'Mwebantu', 'icon': 'globe', 'order': 5},
                            {'name': 'Zambian Eye', 'icon': 'globe', 'order': 6},
                            {'name': 'Breeze FM News', 'icon': 'globe', 'order': 7},
                            {'name': 'Zedgossip', 'icon': 'globe', 'order': 8},
                        ]
                    },
                }
            },
        }

    def create_categories(self, hierarchy_structure):
        """Create categories from hierarchy structure (adds only, no deletion)"""
        created_count = 0
        updated_count = 0
        errors = []
        
        for parent_name, parent_data in hierarchy_structure.items():
            parent_slug = slugify(parent_name)
            
            # Check if parent already exists
            existing_parent = Category.objects.filter(slug=parent_slug).first()
            
            if existing_parent:
                self.stdout.write(self.style.NOTICE(f'📁 Parent exists (skipping): {existing_parent.name}'))
                parent = existing_parent
            else:
                # Create parent (Level 0)
                parent = Category.objects.create(
                    name=parent_name,
                    slug=parent_slug,
                    icon=parent_data['icon'],
                    order=parent_data['order'],
                    description=parent_data.get('description', ''),
                    is_active=True,
                    level=0,
                    parent=None
                )
                self.stdout.write(self.style.SUCCESS(f'📁 Created parent: {parent.name}'))
                created_count += 1
            
            # Create Level 1: Subcategories
            for sub_name, sub_data in parent_data.get('subcategories', {}).items():
                # Create full name with parent context for uniqueness
                full_sub_name = f"{parent_name} - {sub_name}"
                sub_slug = slugify(full_sub_name)
                
                # Check if subcategory already exists
                existing_sub = Category.objects.filter(slug=sub_slug).first()
                
                if existing_sub:
                    self.stdout.write(self.style.NOTICE(f'  📂 Subcategory exists (skipping): {existing_sub.name}'))
                    sub_category = existing_sub
                else:
                    sub_category = Category.objects.create(
                        name=full_sub_name,
                        slug=sub_slug,
                        icon=sub_data.get('icon', parent_data.get('icon', 'folder')),
                        parent=parent,
                        order=sub_data.get('order', 999),
                        description=sub_data.get('description', f'{sub_name} resources for {parent_name}'),
                        is_active=True,
                        level=1
                    )
                    self.stdout.write(self.style.SUCCESS(f'  📂 Created: {sub_category.name}'))
                    created_count += 1
                
                # Create Level 2: Subjects/Courses
                for subject in sub_data.get('subjects', []):
                    # Create full name with full path for uniqueness
                    full_subject_name = f"{parent_name} - {sub_name} - {subject['name']}"
                    subject_slug = slugify(full_subject_name)
                    
                    # Shorten name if too long
                    if len(full_subject_name) > 190:
                        full_subject_name = full_subject_name[:187] + "..."
                    
                    try:
                        # Check if subject already exists
                        existing_subject = Category.objects.filter(slug=subject_slug[:190]).first()
                        
                        if existing_subject:
                            self.stdout.write(self.style.NOTICE(f'    📄 Subject exists (skipping): {existing_subject.name}'))
                        else:
                            subject_category = Category.objects.create(
                                name=full_subject_name,
                                slug=subject_slug[:190],
                                icon=subject.get('icon', 'book'),
                                parent=sub_category,
                                order=subject.get('order', 999),
                                description=subject.get('description', f'{subject["name"]} - {sub_name} level'),
                                is_active=True,
                                level=2
                            )
                            self.stdout.write(self.style.SUCCESS(f'    📄 Created: {subject_category.name}'))
                            created_count += 1
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
        self.stdout.write(self.style.SUCCESS(f'\n✅ College, University, and Newspaper categories added successfully!'))
        self.stdout.write(f'   Created: {created_count}')
        
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