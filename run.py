from core.models import Product
import os, django

# 👇 Replace "config.settings" with your actual project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()
products = Product.objects.filter(category=2)

for obj in products:
    if obj.image and str(obj.image).endswith(".PNG"):
        obj.image.name = obj.image.name.replace(".PNG", ".png")
        obj.save(update_fields=["image"])
        print(f"Updated: {obj.name} → {obj.image.name}")
