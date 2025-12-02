# core/management/commands/build_recommendations.py
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product, ProductRecommendation, ParentCategoryAssignment
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Build recommendation engine (improved TF-IDF + co-occurrence + popularity fallback)."

    def handle(self, *args, **options):
        products = list(Product.objects.all())
        total_products = len(products)
        if not products:
            self.stdout.write(self.style.WARNING("No products found. Exiting."))
            return
        self.stdout.write(self.style.SUCCESS(f"Found {total_products} products."))

        # --- Try to import sklearn ---
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            sklearn_available = True
        except Exception:
            sklearn_available = False
            self.stdout.write(self.style.WARNING("sklearn not available — skipping TF-IDF content recommendations."))

        # build a richer text representation per product
        def parent_name_for(p):
            try:
                pa = ParentCategoryAssignment.objects.filter(category=p.category).first()
                return pa.parent.name if pa and pa.parent else ""
            except Exception:
                return ""

        def build_text(p):
            parts = [
                (p.name or ""),
                (p.short_description or ""),
                (p.description or ""),
                (p.metal or ""),
                (p.category.name if getattr(p, "category", None) else ""),
                parent_name_for(p) or "",
            ]
            # join non-empty parts, limit length for performance
            text = " ".join([str(x) for x in parts if x])
            if not text.strip():
                # fallback to name to ensure no-empty corpus entry
                text = str(p.name or f"product_{p.id}")
            return text

        corpus = [build_text(p) for p in products]

        similarity = None
        if sklearn_available:
            # configure vectorizer to be robust: include unigrams & bigrams, limit features for memory
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=25000)
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
                # compute cosine similarity
                similarity = cosine_similarity(tfidf_matrix, dense_output=False)
                self.stdout.write(self.style.SUCCESS("TF-IDF content similarity matrix computed."))
            except Exception as exc:
                similarity = None
                self.stdout.write(self.style.WARNING(f"TF-IDF failed: {exc}"))

        # initialize rec_map
        rec_map = {p.id: [] for p in products}

        # content-based recommendations
        if similarity is not None:
            try:
                # similarity may be sparse or numpy array — handle both
                import numpy as np
                for idx, product in enumerate(products):
                    # get row of similarities
                    row = similarity[idx]
                    # if row is a numpy array
                    if hasattr(row, "toarray"):
                        row_arr = row.toarray().ravel()
                    else:
                        row_arr = np.array(row).ravel()
                    # argsort descending, skip itself
                    sim_indices = row_arr.argsort()[::-1]
                    top_indices = [i for i in sim_indices if i != idx][:20]  # take more to mix later
                    rec_ids = [products[i].id for i in top_indices]
                    rec_map[product.id].extend(rec_ids)
                self.stdout.write(self.style.SUCCESS("Content-based recommendations generated."))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Content-based post-processing failed: {exc}"))

        # behavior co-occurrence (if pandas + interactions exist)
        try:
            from core.models import UserProductInteraction
            import pandas as pd
            interactions = list(UserProductInteraction.objects.all().values("session_key", "product_id", "weight"))
            if interactions:
                df = pd.DataFrame(interactions)
                # ensure we have session-level grouping; fall back to user if session not present
                if "session_key" not in df.columns or df["session_key"].isnull().all():
                    if "user_id" in df.columns:
                        df["session_key"] = df["user_id"].astype(str)
                    else:
                        df["session_key"] = "anon"

                pivot = df.pivot_table(index="session_key", columns="product_id", values="weight", aggfunc="sum", fill_value=0)
                cooc = pivot.T.dot(pivot)  # co-occurrence matrix
                # for each product id in the co-occurrence matrix, add top co-occurring ids
                for pid in cooc.index:
                    try:
                        scores = cooc.loc[pid].sort_values(ascending=False)
                        # drop itself and take top 10
                        scores = scores[scores.index != pid][:10]
                        ids = list(scores.index)
                        if pid in rec_map:
                            rec_map[int(pid)].extend([int(x) for x in ids])
                        else:
                            rec_map[int(pid)] = [int(x) for x in ids]
                    except Exception:
                        continue
                self.stdout.write(self.style.SUCCESS("Behavioral co-occurrence recommendations computed."))
            else:
                self.stdout.write(self.style.WARNING("No user interactions found — skipping behavior-based recommendations."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Behavioral recommendations skipped: {exc}"))

        # Popularity fallback: top products by number of interactions (if interactions exist)
        popular_ids = []
        try:
            from django.db.models import Count
            popular_qs = Product.objects.all().annotate(cnt=Count("userproductinteraction")).order_by("-cnt")[:50]
            popular_ids = [p.id for p in popular_qs]
            if popular_ids:
                self.stdout.write(self.style.SUCCESS(f"Popularity fallback prepared ({len(popular_ids)} items)."))
        except Exception:
            popular_ids = [p.id for p in products[:50]]

        # Write final recommendations to DB (unique preserve order, apply limit, fallback to popular)
        MAX_RECS = 10
        saved = 0
        with transaction.atomic():
            for pid, id_list in rec_map.items():
                # unique-preserve order
                seen = set()
                final = []
                for x in id_list:
                    if x is None:
                        continue
                    if x not in seen and x != pid:
                        seen.add(x)
                        final.append(int(x))
                    if len(final) >= MAX_RECS:
                        break

                # if no recs, use popular_ids as fallback (exclude itself)
                if not final:
                    for x in popular_ids:
                        if x != pid and x not in final:
                            final.append(x)
                        if len(final) >= MAX_RECS:
                            break

                # ensure final contains valid existing product ids
                valid_final = []
                existing_ids = set(p.id for p in products)
                for rid in final:
                    if rid in existing_ids and rid != pid:
                        valid_final.append(rid)
                    if len(valid_final) >= MAX_RECS:
                        break

                # Save
                try:
                    product = Product.objects.get(pk=pid)
                    obj, created = ProductRecommendation.objects.get_or_create(product=product)
                    obj.recommended_ids = valid_final
                    obj.save()
                    saved += 1
                except Product.DoesNotExist:
                    continue

        self.stdout.write(self.style.SUCCESS(f"Recommendations computed and saved for {saved} products."))

