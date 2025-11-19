import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.apps import apps

print("=" * 80)
print("DJANGO MODELS vs DATABASE SCHEMA CHECK")
print("=" * 80)

# Get all models
all_models = apps.get_models()

issues = []

for model in all_models:
    if hasattr(model, '_meta') and hasattr(model._meta, 'db_table'):
        table_name = model._meta.db_table
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        # Skip Django internal tables
        if table_name.startswith('auth_') or table_name.startswith('django_'):
            continue
        
        print(f"\nModel: {model_name}")
        print(f"Table: {table_name}")
        
        # Get model fields
        model_fields = {}
        for field in model._meta.get_fields():
            if hasattr(field, 'column'):
                model_fields[field.column] = field.get_internal_type()
        
        # Try to query actual table columns
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, [table_name])
                
                db_columns = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Find discrepancies
                model_cols = set(model_fields.keys())
                db_cols = set(db_columns.keys())
                
                missing_in_model = db_cols - model_cols
                missing_in_db = model_cols - db_cols
                
                if missing_in_model:
                    issue = f"  ⚠ Missing in model: {', '.join(missing_in_model)}"
                    print(issue)
                    issues.append((model_name, table_name, issue))
                
                if missing_in_db:
                    issue = f"  ⚠ Missing in DB: {', '.join(missing_in_db)}"
                    print(issue)
                    issues.append((model_name, table_name, issue))
                
                if not missing_in_model and not missing_in_db:
                    print("  ✓ Model matches database")
                    
        except Exception as e:
            print(f"  ✗ Error checking table: {e}")

print("\n" + "=" * 80)
print("SUMMARY OF ISSUES")
print("=" * 80)

if issues:
    for model_name, table_name, issue in issues:
        print(f"\n{model_name} ({table_name}):")
        print(issue)
else:
    print("\n✓ No issues found - all models match database schema")

print("\n" + "=" * 80)
