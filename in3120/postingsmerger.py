# pylint: disable=missing-module-docstring

from typing import Iterator
from .posting import Posting


class PostingsMerger:
    """
    Utility class for merging posting lists.

    It is currently left unspecified what to do with the term frequency field
    in the returned postings when document identifiers overlap. Different
    approaches are possible, e.g., an arbitrary one of the two postings could
    be returned, or the posting having the smallest/largest term frequency, or
    a new one that produces an averaged value, or something else.
    """

    @staticmethod
    def intersection(
        iter1: Iterator[Posting], iter2: Iterator[Posting]
    ) -> Iterator[Posting]:
        """
        A generator that yields a simple AND(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        # Followed the pseudocode from the book (p. 48 figure 1.6)
        try:
            left = next(iter1)
            right = next(iter2)

            while True:
                if left.document_id == right.document_id:
                    yield left
                    left = next(iter1)
                    right = next(iter2)

                elif left.document_id < right.document_id:
                    left = next(iter1)

                else:
                    right = next(iter2)

        except StopIteration:
            return

    @staticmethod
    def union(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple OR(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """

        # Retrieve the first postings from the iterators, and check if the postings are empty
        try:
            left = next(iter1)
        except StopIteration:
            left = None

        try:
            right = next(iter2)
        except StopIteration:
            right = None

        # Loop through the postings as long as left nor right is None
        while left is not None and right is not None:
            # Doc_id is the same, yield one of them and advanve both iterators
            if left.document_id == right.document_id:
                yield left
                try:
                    left = next(iter1)
                except StopIteration:
                    left = None  # Has to set to empty, since stupid.

                try:
                    right = next(iter2)
                except StopIteration:
                    right = None

            # Advance the first list to it matches the second list
            elif left.document_id < right.document_id:
                yield left
                try:
                    left = next(iter1)
                except StopIteration:
                    left = None
            else:
                yield right
                try:
                    right = next(iter2)
                except StopIteration:
                    right = None

        # Yield the posting list that is not None, set to None in while loop. (Not a fan)
        if left is not None:
            yield left
            yield from iter1

        if right is not None:
            yield right
            yield from iter2

    @staticmethod
    def difference(
        iter1: Iterator[Posting], iter2: Iterator[Posting]
    ) -> Iterator[Posting]:
        """
        A generator that yields a simple ANDNOT(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        # Check if empty
        try:
            left = next(iter1)
        except StopIteration:
            left = None
        try:
            right = next(iter2)
        except StopIteration:
            right = None

        while left is not None and right is not None:
            if left.document_id == right.document_id:

                # Trying to iterate to the next posting
                try:
                    left = next(iter1)
                except StopIteration:
                    left = None
                try:
                    right = next(iter2)
                except StopIteration:
                    right = None

            # Never intrested of yielding right. So only yield left and move along.
            elif left.document_id < right.document_id:
                yield left
                try:
                    left = next(iter1)
                except StopIteration:
                    left = None
            else:
                try:
                    right = next(iter2)
                except StopIteration:
                    right = None

        # Yield the rest of the postings (for that time right is shorter than left)
        if left is not None:
            yield left
            yield from iter1
