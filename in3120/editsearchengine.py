# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long
# pylint: disable=fixme
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments

import math
from typing import Iterator, Dict, Any, Callable
from .edittable import EditTable
from .normalizer import Normalizer
from .sieve import Sieve
from .tokenizer import Tokenizer
from .trie import Trie


class EditSearchEngine:
    """
    Realizes a simple edit distance lookup engine, that, given a larger set of strings encoded
    in a trie, finds all strings in the trie that are close to a given query string in terms of edit
    distance.
    See the paper "Tries for Approximate String Matching" by Shang and Merrett for details. This
    implementation assumes that we set an upper bound on the allowed edit distance (treating anything
    above this bound as infinity and non-retrievable), and that this upper bound is relatively small.
    Imposing a small upper bound allows us to prune the search space and make the search reasonably
    efficient.
    """

    def __init__(self, trie: Trie, normalizer: Normalizer, tokenizer: Tokenizer):
        self.__trie = trie
        self.__normalizer = normalizer  # The same as was used for trie building.
        self.__tokenizer = tokenizer  # The same as was used for trie building.

    def evaluate(self, query: str, options: dict) -> Iterator[Dict[str, Any]]:
        """
        Locates all strings in the trie that are no more than K edit errors away from the query string.

        The matching strings, if any, are scored and only the highest-scoring matches are yielded
        back to the client as dictionaries having the keys "score" (float), "distance" (int) and
        "match" (str).

        The client can supply a dictionary of options that controls the query evaluation process:
        Supported dictionary keys include "upper_bound" (int), "candidate_count" (int),
        "hit_count" (int), "first_n" (int), and "scoring" (str).
        """
        # Tokenize and join to be robust to nuances in whitespace.
        tokens = self.__tokenizer.tokens(self.__normalizer.canonicalize(query))
        tokens = ((self.__normalizer.normalize(t), _) for t, _ in tokens)
        query = self.__tokenizer.join(tokens)

        # The upper bound for the edit distance we accept between the query and a match. Assumed to be
        # a small number, e.g., 1, 2, or 3. The lower we set the upper bound, the more we can prune
        # the search space, and the more efficient the lookup will be.
        upper_bound = max(0, options.get("upper_bound", 1))

        # The maximum number of candidate matches we score.
        candidate_count = max(1, options.get("candidate_count", 10000))

        # The maximum number of scored matches we will emit.
        hit_count = max(1, min(100, options.get("hit_count", 10)))

        # Assume that the N first characters are correct? This significantly prunes down the search
        # space and can give a performance boost. However, we get worse recall if the assumption is
        # incorrect.
        first_n = max(0, min(len(query), options.get("first_n", 0)))

        # Make some modifications to our starting point, if needed.
        head = query[:first_n]
        tail = query[first_n:]
        root = self.__trie if first_n == 0 else self.__trie.consume(head)

        # The available scoring functions that the client can choose from. High
        # scores are better than low scores. The "lopresti" function is lifted
        # from https://www.cse.lehigh.edu/~lopresti/Publications/1996/sdair96.pdf.
        scorers = {
            "negated": lambda d, q, c: -d,
            "normalized": lambda d, q, c: 1.0 - (d / (first_n + max(len(q), len(c)))),
            "lopresti": lambda d, q, c: 1.0
            / math.exp(d / (first_n + max(len(q), len(c)) - d)),
        }

        # The selected scoring function to apply to candidate matches.
        scorer = scorers.get(options.get("scoring", "normalized"), None)
        assert scorer is not None

        # For keeping track of scored candidate matches. Only retains the highest-scoring ones.
        sieve = Sieve(hit_count)

        # The edit table object that we update as we traverse the trie. Two strings that share
        # a prefix of length N also share the N first columns in the edit table. Hence, as we
        # traverse the trie we can avoid recomputing large parts of the table.
        table = EditTable(tail, "?" * 10, False)

        # Receives matches from the search, as they are found. The search aborts if the callback
        # returns False, i.e., when we have received sufficiently many candidate matches.
        # My implementation until line 112.

        counter = 0 # max number of candidates
        def callback(distance: int, candidate: str, meta: Any) -> bool:
            nonlocal counter

            if counter >= candidate_count:
                return False

            if distance <= upper_bound:
                score = scorer(distance, query, candidate)
                sieve.sift(score, (distance, candidate, meta))
                counter += 1 # Not yet at the max number of candidates

                return True
            return False

        # Search! We receive and sift results via the callback.
        if root:
            self.__dfs(root, 0, table, upper_bound, callback)

        # Emit the best matches!
        for score, (distance, match, meta) in sieve.winners():
            yield {"score": score, "distance": distance, "match": head + match, "meta": meta}

    def __dfs(self, node: Trie, level: int, table: EditTable, upper_bound: int,
            callback: Callable[[float, str, Any], bool],) -> bool:
        """
        Does a recursive depth-first search in the trie, pruning away paths that cannot lead
        to matches with a sufficiently low edit cost. See paper by Shang and Merrett for a
        detailed discussion.

        Returns True unless the supplied callback tells us to abort the search.

        As this implementation is recursive, the call stack might blow up if we go really
        many levels deep into the trie. That should not be an issue as the primary use case
        for this search is to consult a simple spellchecking dictionary of strings all having
        reasonable lengths, but could merit a second look if we look to apply this to other
        use cases.

        My implementation
        """
        if node.is_final():
            if not callback(table.distance(), "".join(table._candidate), node.get_meta()):
                return False

        # Go over the children
        for candidata_char in node.transitions():
            # Save the table
            if level < len(table._candidate):
                original_char = table._candidate[level]
            else:
                original_char = "?"

            # Add the candidate character to the table and resume the search
            table.update2(level, candidata_char)
            child = node.consume(candidata_char)
            self.__dfs(child, level + 1, table, upper_bound, callback)

            table._candidate[level] = original_char

        return True
