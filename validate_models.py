"""
Script to validate all SQLAlchemy models.

This script:
1. Imports all models
2. Checks relationships
3. Verifies table definitions
4. Reports any issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def validate_models():
    """Validate all SQLAlchemy models."""
    print("=" * 60)
    print("SQLAlchemy Models Validation")
    print("=" * 60)

    try:
        # Import database base
        from src.core.database import Base

        print("\n✅ Database base imported successfully")

        # Import all models
        from src.models import (
            AuditLog,
            EmailNotification,
            Event,
            EventStatus,
            Order,
            OrderItem,
            OrderStatus,
            PaymentStatus,
            PaymentTransaction,
            Promoter,
            Ticket,
            TicketStatus,
            TicketTier,
            User,
            UserRole,
            Waitlist,
        )

        print("✅ All models imported successfully")

        # List all tables
        tables = Base.metadata.tables.keys()
        print(f"\n📊 Registered Tables ({len(tables)}):")
        for table_name in sorted(tables):
            table = Base.metadata.tables[table_name]
            column_count = len(table.columns)
            fk_count = len([c for c in table.columns if c.foreign_keys])
            print(f"   • {table_name:25} - {column_count:2} columns, {fk_count:2} foreign keys")

        # Check relationships
        print(f"\n🔗 Model Relationships:")

        models_with_relationships = [
            ("User", User),
            ("Promoter", Promoter),
            ("Event", Event),
            ("TicketTier", TicketTier),
            ("Order", Order),
            ("OrderItem", OrderItem),
            ("Ticket", Ticket),
            ("Waitlist", Waitlist),
            ("PaymentTransaction", PaymentTransaction),
        ]

        for model_name, model_class in models_with_relationships:
            relationships = [
                rel.key for rel in model_class.__mapper__.relationships
            ]
            if relationships:
                print(f"   • {model_name:20} → {', '.join(relationships)}")

        # Summary
        print("\n" + "=" * 60)
        print("✅ VALIDATION SUCCESSFUL")
        print("=" * 60)
        print(f"   Total Tables: {len(tables)}")
        print(f"   Total Models: {len(models_with_relationships)}")
        print(f"   Status: All models are valid and ready for use")
        print("=" * 60)

        return True

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"\n❌ Validation Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_models()
    sys.exit(0 if success else 1)
