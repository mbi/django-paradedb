from testapp.models import Item, Review

from django.test import TestCase

from paradedb.functions import Highlight, Score
from django.db.models import Q


class ParadeDBCase(TestCase):
    fixtures = ["testapp/test_data.json"]

    def test_has_loaded_data(self):
        self.assertTrue(Item.objects.count() > 100)

    def test_search_lookup(self):
        self.assertTrue(
            Item.objects.filter(
                description__term_search="Colpoys then attempted to isolate his crew"
            ).count()
            > 80
        )

    def test_phrase_search_lookup(self):
        self.assertTrue(
            Item.objects.filter(
                description__phrase_search="Colpoys then attempted to isolate his crew"
            ).count()
            == 1
        )

    def test_phrase_prefix_search_lookup(self):
        self.assertTrue(
            Item.objects.filter(
                description__phrase_search="Colpoys then attemp*"
            ).count()
            == 0
        )

        self.assertTrue(
            Item.objects.filter(
                description__phrase_prefix_search="Colpoys then attemp*"
            ).count()
            == 1
        )

    def test_fuzzy_lookup(self):
        self.assertTrue(
            Item.objects.filter(description__fuzzy_term_search="atempted crwe").count()
            > 50
        )

    def test_fuzzy_phrase_lookup(self):
        self.assertTrue(
            Item.objects.filter(
                description__fuzzy_phrase_search="Cololys attempte to isoate his crew"
            ).count()
            == 1
        )

    def test_json_search_lookup(self):
        # Test JSON search with string input
        self.assertTrue(
            Item.objects.filter(
                description__json_search='{"term": {"value": "Colpoys"}}'
            ).exists()
        )

        # Test JSON search with field specification as string
        self.assertTrue(
            Item.objects.filter(
                description__json_search='{"term": {"field": "description", "value": "Royal Navy"}}'
            ).exists()
        )
        
        # Test JSON search with dictionary input
        self.assertTrue(
            Item.objects.filter(
                description__json_search={"term": {"value": "Colpoys"}}
            ).exists()
        )
        
        # Test JSON search with dictionary input and field specification
        self.assertTrue(
            Item.objects.filter(
                description__json_search={"term": {"field": "description", "value": "Royal Navy"}}
            ).exists()
        )
        
        # Test fuzzy matching using JSON syntax
        self.assertTrue(
            Item.objects.filter(
                description__json_search={
                    "fuzzy": {
                        "field": "description",
                        "value": "atempted crwe",  # Misspelled "attempted crew"
                        "distance": 2
                    }
                }
            ).exists()
        )
        
        # Test fuzzy phrase matching using JSON syntax
        # Check if we get any results with a less restrictive match
        self.assertTrue(
            Item.objects.filter(
                description__json_search={
                    "fuzzy": {
                        "field": "description",
                        "value": "Cololys attempte to isoate his crew",  # Misspelled phrase
                        "distance": 2,
                        "conjunction_mode": False  # Match any term
                    }
                }
            ).exists()
        )
        
        # Try results with paradedb.match function syntax directly
        self.assertTrue(
            Item.objects.filter(
                description__json_search='{"match": {"field": "description", "value": "Colpoys attempted to isolate", "conjunction_mode": true}}'
            ).exists()
        )

    def test_score_sorting(self):
        # annotated but unsorted
        qs = Item.objects.filter(description__term_search="music").annotate(
            score=Score()
        )
        item1, item2, item3 = qs[:3]
        self.assertTrue(item1.score < item2.score)

        # Sorted qs
        item1, item2, item3 = qs.order_by("-score")[:3]
        self.assertTrue(item1.score > item2.score)

    def test_highlighting(self):
        item = (
            Item.objects.filter(description__term_search="Fleischmann")
            .annotate(description_hl=Highlight("description"))
            .first()
        )
        self.assertTrue(
            "Hungarian-American businessman Charles Louis <em>Fleischmann</em>"
            in item.description_hl
        )
        self.assertFalse(
            "Hungarian-American businessman Charles Louis <em>Fleischmann</em>"
            in item.description
        )

        item = (
            Item.objects.filter(description__term_search="Fleischmann")
            .annotate(
                description_hl=Highlight(
                    "description", start_tag="<start>", end_tag="<end>"
                )
            )
            .first()
        )
        self.assertTrue(
            "Hungarian-American businessman Charles Louis <start>Fleischmann<end>"
            in item.description_hl
        )

    def test_query_escapes(self):
        Item.objects.all().delete()
        for kw in [
            "+",
            "^",
            "`",
            ":",
            "{",
            "}",
            '"',
            "[",
            "]",
            "(",
            ")",
            "<",
            ">",
            "~",
            "!",
            "\\",
            "\\*",
            "",
        ]:
            desc = f"desc{kw}desc"
            name = f"name{kw}name"
            item_in = Item.objects.create(name=name, description=desc, rating=0.1)

            qs = Item.objects.filter(description__term_search=desc)
            result_count = qs.count()

            self.assertEqual(result_count, 1)
            item_out = qs.get()
            self.assertEqual(item_in.pk, item_out.pk)
            self.assertEqual(item_in.name, item_out.name)

            Item.objects.all().delete()

    def test_joins(self):
        self.assertTrue(
            Review.objects.filter(
                item__description__term_search="Unsourced material"
            ).exists()
        )

        self.assertTrue(
            Review.objects.filter(
                item__description__phrase_search="Unsourced material"
            ).exists()
        )

        self.assertTrue(
            Review.objects.filter(
                item__description__fuzzy_term_search="Unsourcad matrial"
            ).exists()
        )
        
        # Test join using json_search with string input
        self.assertTrue(
            Review.objects.filter(
                item__description__json_search='{"term": {"value": "Unsourced material"}}'
            ).exists()
        )
        
        # Test join using json_search with dictionary input
        self.assertTrue(
            Review.objects.filter(
                item__description__json_search={"term": {"value": "Unsourced material"}}
            ).exists()
        )
        
        # Test join using json_search with fuzzy query
        self.assertTrue(
            Review.objects.filter(
                item__description__json_search={
                    "fuzzy": {
                        "field": "description",
                        "value": "Unsourcad matrial",  # Misspelled
                        "distance": 2
                    }
                }
            ).exists()
        )

    def test_joined_scoring(self):
        reviews = (
            Review.objects.filter(
                item__description__fuzzy_phrase_search="Province writer"
            )
            .annotate(score=Score("item__description"))
            .order_by("-score")
        )

        self.assertTrue(reviews.count() == 2)
        r1, r2 = reviews

        assert r1.score > r2.score


    def test_joined_self_scoring(self):

        reviews = (
            Review.objects.filter(
                Q(item__description__fuzzy_phrase_search="Province writer") |
                Q(review__fuzzy_phrase_search="something somethang"),
            )
            .annotate(score=Score("review"))
            .order_by("-score")
        )

        self.assertTrue(reviews.count() == 2)
        r1, r2 = reviews

        assert r1.score > r2.score
