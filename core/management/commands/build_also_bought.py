# core/management/commands/build_also_bought.py
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product, ProductRecommendation, UserProductInteraction
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Compute 'Customers also bought' using co-occurrence from order (purchase) events."

    def handle(self, *args, **options):
        # 1) Try to use order events first
        qs = UserProductInteraction.objects.filter(event__iexact="order").values("session_key", "product_id")
        if not qs.exists():
            self.stdout.write(self.style.WARNING("No order events found — falling back to cart events."))
            qs = UserProductInteraction.objects.filter(event__iexact="cart").values("session_key", "product_id")

            if not qs.exists():
                self.stdout.write(self.style.WARNING("No cart/order events found. Cannot compute also-bought."))
                return

        # 2) build order/session -> set(product_id)
        sessions = {}
        for r in qs:
            sk = r.get("session_key") or "anon"
            pid = int(r.get("product_id"))
            sessions.setdefault(sk, set()).add(pid)

        # 3) compute co-occurrence counts
        cooc = defaultdict(lambda: defaultdict(int))
        for prod_set in sessions.values():
            prod_list = list(prod_set)
            for i in range(len(prod_list)):
                for j in range(len(prod_list)):
                    if prod_list[i] == prod_list[j]:
                        continue
                    cooc[prod_list[i]][prod_list[j]] += 1

        if not cooc:
            self.stdout.write(self.style.WARNING("No co-occurrence counts produced."))
            return

        # 4) for each product, pick top N co-occurring product ids
        MAX = 10
        saved = 0
        all_product_ids = set(Product.objects.values_list("id", flat=True))

        with transaction.atomic():
            for pid, neighbors in cooc.items():
                # sort neighbors by count descending
                sorted_neighbors = sorted(neighbors.items(), key=lambda x: x[1], reverse=True)
                top_ids = [nid for nid, score in sorted_neighbors if nid in all_product_ids and nid != pid][:MAX]

                # save to ProductRecommendation.also_bought_ids (create object if needed)
                try:
                    product = Product.objects.get(pk=pid)
                except Product.DoesNotExist:
                    continue

                pr, created = ProductRecommendation.objects.get_or_create(product=product)
                pr.also_bought_ids = top_ids
                pr.save()
                saved += 1

        self.stdout.write(self.style.SUCCESS(f"Computed and saved also-bought for {saved} products."))
