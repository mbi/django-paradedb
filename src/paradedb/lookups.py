from django.db.models import Field
from django.db.models.lookups import PostgresOperatorLookup


@Field.register_lookup
class BaseParadeDBLookup(PostgresOperatorLookup):
    """
    https://docs.paradedb.com/documentation/full-text/overview#basic-usage

    SELECT description, rating, category
    FROM mock_items
    WHERE description @@@ 'shoes'
    LIMIT 5;
    """

    lookup_name = "term_search"
    postgres_operator = "@@@"
    prepare_rhs = True

    def get_prep_lookup(self):
        rhs = super().get_prep_lookup()
        return (
            rhs.replace(":", r"\:")
            .replace("[", r"\[")
            .replace("]", r"\]")
            .replace("(", r"\(")
            .replace(")", r"\)")
            .replace("'", r"\'")
            .replace('"', r"\"")
            .replace("-", r"\-")
            .replace("+", r"\+")
            .replace("*", r"\*")
            .replace("^", r"\^")
            .replace("`", r"\`")
            .replace("{", r"\{")
            .replace("}", r"\}")
        )


@Field.register_lookup
class PhraseParadeDBLookup(BaseParadeDBLookup):
    """
    https://docs.paradedb.com/documentation/full-text/phrase

    SELECT description, rating, category
    FROM mock_items
    WHERE description @@@ '"plastic keyboard"';
    """

    lookup_name = "phrase_search"

    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        return f"'\"{rhs_params[0]}\"'", []


@Field.register_lookup
class PhrasePrefixParadeDBLookup(BaseParadeDBLookup):
    """
    https://docs.paradedb.com/documentation/full-text/phrase#phrase-prefix

    The * prefix operator allows for the last term in the phrase query to be
    the prefix of another word. For instance, "plastic keyb"* matches plastic
    keyboard.

    SELECT description, rating, category
    FROM mock_items
    WHERE description @@@ '"plastic keyb"*';
    """

    lookup_name = "phrase_prefix_search"

    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        return f"'\"{rhs_params[0]}\"*'", []


class BaseFuzzyParadeDBLookup(BaseParadeDBLookup):
    """
    https://docs.paradedb.com/documentation/guides/autocomplete#fuzzy-term
    https://docs.paradedb.com/documentation/guides/autocomplete#fuzzy-phrase

    SELECT description, rating, category FROM mock_items
    WHERE id @@@ paradedb.match(
        field => 'description',
        value => 'ruining shoez'
    ) ORDER BY rating DESC;

    """

    def process_lhs(self, compiler, connection, lhs=None):
        id_field_name = compiler.query.model._meta.pk.name

        # This is so horribly awkward and brittle,
        # there must be a proper way of doing this
        lhs, _ = super().process_lhs(compiler, connection, lhs=lhs)
        tbl = lhs.replace('"', "").rsplit(".", 1)[0]

        return f'"{tbl}"."{id_field_name}"', []

    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        lhs, _ = super().process_lhs(compiler, connection)
        col = lhs.replace('"', "").rsplit(".", 1)[-1]
        return (
            "paradedb.match(field => %s, value => %s, "
            f"conjunction_mode => {self.match_all_terms}, "
            f"distance => {self.distance})"
        ), [col, rhs_params[0]]


@Field.register_lookup
class FuzzyParadeDBLookup(BaseFuzzyParadeDBLookup):
    lookup_name = "fuzzy_term_search"
    match_all_terms = "false"
    distance = 2


@Field.register_lookup
class FuzzyPhraseParadeDBLookup(BaseFuzzyParadeDBLookup):
    lookup_name = "fuzzy_phrase_search"
    match_all_terms = "true"
    distance = 2


import json

@Field.register_lookup
class JsonParadeDBLookup(BaseParadeDBLookup):
    """
    Allows using ParadeDB's JSON-based syntax for advanced queries.
    
    Accepts either a JSON string or a Python dictionary which will be converted to JSON.

    Example with a string:
    SELECT description, rating, category
    FROM mock_items
    WHERE description @@@ '{"term": {"field": "description", "value": "keyboard"}}';
    
    Example with a Python dictionary:
    Item.objects.filter(
        description__json_search={"term": {"field": "description", "value": "keyboard"}}
    )
    """

    lookup_name = "json_search"
    
    def as_sql(self, compiler, connection):
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        
        # Build the SQL condition
        sql = "%s %s %s" % (lhs_sql, self.postgres_operator, rhs_sql)
        return sql, lhs_params + rhs_params
    
    def process_rhs(self, compiler, connection):
        value = self.rhs
        
        # If it's already a string, assume it's a valid JSON string
        if isinstance(value, str):
            return "'%s'" % value.replace("'", "''"), []
        
        # Otherwise convert dict to JSON string
        if isinstance(value, (dict, list)):
            json_str = json.dumps(value)
            return "'%s'" % json_str.replace("'", "''"), []
            
        # Fallback (should not happen)
        return "'%s'" % str(value).replace("'", "''"), []
