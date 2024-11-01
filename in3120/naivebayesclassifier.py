# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import math
from collections import Counter
from typing import Any, Dict, Iterable, Iterator
from .dictionary import InMemoryDictionary
from .normalizer import Normalizer
from .tokenizer import Tokenizer
from .corpus import Corpus


class NaiveBayesClassifier:
    """
    Defines a multinomial naive Bayes text classifier. For a detailed primer, see
    https://nlp.stanford.edu/IR-book/html/htmledition/naive-bayes-text-classification-1.html.
    """

    def __init__(self, training_set: Dict[str, Corpus], fields: Iterable[str],
                 normalizer: Normalizer, tokenizer: Tokenizer):
        """
        Trains the classifier from the named fields in the documents in the
        given training set.
        """
        # Used for breaking the text up into discrete classification features.
        self.__normalizer = normalizer
        self.__tokenizer = tokenizer

        # The vocabulary we've seen during training.
        self.__vocabulary = InMemoryDictionary()

        # Maps a category c to the logarithm of its prior probability,
        # i.e., c maps to log(Pr(c)).
        self.__priors: Dict[str, float] = {}

        # Maps a category c and a term t to the logarithm of its conditional probability,
        # i.e., (c, t) maps to log(Pr(t | c)).
        self.__conditionals: Dict[str, Dict[str, float]] = {}

        # Maps a category c to the denominator used when doing Laplace smoothing.
        self.__denominators: Dict[str, int] = {}

        # Train the classifier, i.e., estimate all probabilities.
        self.__compute_priors(training_set)
        self.__compute_vocabulary(training_set, fields)
        self.__compute_posteriors(training_set, fields)

    def __compute_priors(self, training_set) -> None:
        """
        Estimates all prior probabilities (or, rather, log-probabilities) needed for
        the naive Bayes classifier.

        Compute the frequency of each category in the training set. Normalize to get the probability, 
        then take the log to avoid underflow.
        """
        total_doc = sum(map(len, training_set.values()))

        for category, corpus in training_set.items():
            prior = len(corpus) / total_doc
            self.__priors[category] = math.log(prior)

    def __compute_vocabulary(self, training_set, fields) -> None:
        """
        Builds up the overall vocabulary as seen in the training set.
        """
        for category, corpus in training_set.items():
            for document in corpus:
                for field in fields:
                    content = document.get_field(field, "")
                    terms = self.__get_terms(content)
                    for term in terms:
                        self.__vocabulary.add_if_absent(term)


    def __compute_posteriors(self, training_set, fields) -> None:
        """
        Estimates all conditional probabilities (or, rather, log-probabilities) needed for
        the naive Bayes classifier.

        P(language | term) = (P(term | language) * P(language)) / P(term) , where language = class, term = feature 

        P(term | language) = (count(term in category) + 1) / (count(all terms in category) + |V|) , where |V| = vocabulary size
        """
        term_counts_per_category = {}

        # Counting the terms per category
        for category, corpus in training_set.items():
                term_counts = Counter()

                for document in corpus:
                    for field in fields:
                        content = document.get_field(field, "")
                        terms = self.__get_terms(content)
                        term_counts.update(terms)

                # Store term counts and total terms
                self.__denominators[category] = sum(term_counts.values()) + len(self.__vocabulary)
                term_counts_per_category[category] = term_counts

        # Compute the conditional probabilities P(term | language)
        for category, term_counts in term_counts_per_category.items():
                self.__conditionals[category] = {}

                for term, _ in self.__vocabulary:
                    count = term_counts.get(term, 0) + 1  # Add-one smoothing (numerator)
                    denominator = self.__denominators[category] 
                    conditional_probability = count / denominator
                    self.__conditionals[category][term] = math.log(conditional_probability)  # Store log-probability for stability

    def __get_terms(self, buffer) -> Iterator[str]:
        """
        Processes the given text buffer and returns the sequence of normalized
        terms as they appear. Both the documents in the training set and the buffers
        we classify need to be identically processed.
        """
        tokens = self.__tokenizer.strings(self.__normalizer.canonicalize(buffer))
        return (self.__normalizer.normalize(t) for t in tokens)

    def get_prior(self, category: str) -> float:
        """
        Given a category c, returns the category's prior log-probability log(Pr(c)).
        This is an internal detail having public visibility to facilitate testing.
        """
        return self.__priors[category]

    def get_posterior(self, category: str, term: str) -> float:
        """
        Given a category c and a term t, returns the posterior log-probability log(Pr(t | c)).
        This is an internal detail having public visibility to facilitate testing.
        """
        if term not in self.__vocabulary:
            return math.log(1/self.__denominators[category])
        return self.__conditionals[category][term]
        

    def classify(self, buffer: str) -> Iterator[Dict[str, Any]]:
        """
        Classifies the given buffer according to the multinomial naive Bayes rule. The computed (score, category) pairs
        are emitted back to the client via the supplied callback sorted according to the scores. The reported scores
        are log-probabilities, to minimize numerical underflow issues. Logarithms are base e.

        The results yielded back to the client are dictionaries having the keys "score" (float) and
        "category" (str).
        """
        terms = list(self.__get_terms(buffer))
        scores = {}
                
        for category in self.__priors:
            score = self.get_prior(category)

            for term in terms:
                score += self.get_posterior(category, term)

            scores[category] = score
            
        # sort <category, score> pairs by score. biggest score first 
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        
        for category, score in sorted_scores:
            yield {"category": category, "score": score}

    def _get_vocabulary(self) -> set:
        """
        Use for testing. Made own tests for testing each function in the NaiveBayesClassifier class.
        """
        return set(term for term, _ in set(self.__vocabulary))