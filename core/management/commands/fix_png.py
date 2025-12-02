from django.core.management.base import BaseCommand
from core.models import Product

class Command(BaseCommand):
    help = "Fix image filenames with .PNG → .png (only for category=1)"

    def handle(self, *args, **options):
        # Filter only products in category=1
        qs = Product.objects.filter(category_id=1)

        count = 0
        for obj in qs:
            if obj.image and str(obj.image).endswith(".png"):
                old = obj.image.name
                obj.image.name = obj.image.name.replace(".png", ".PNG")
                obj.save(update_fields=["image"])
                self.stdout.write(f"Updated {old} → {obj.image.name}")
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Fixed {count} products in category=1"))
