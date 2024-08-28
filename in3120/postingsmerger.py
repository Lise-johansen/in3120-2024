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
    def intersection(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple AND(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        # Followed the pseudocode from the book (p. 48 figure 1.6)
        try:
            p1 = next(iter1)
            p2 = next(iter2)
            
            while True:
                if p1.document_id == p2.document_id:
                    yield p1
                    p1 = next(iter1)
                    p2 = next(iter2)

                elif p1.document_id < p2.document_id:
                    p1 = next(iter1)

                else:
                    p2 = next(iter2)


        except StopIteration:
            return

        # raise NotImplementedError("You need to implement this as part of the obligatory assignment.")

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
            p1 = next(iter1)
        except StopIteration:
            p1 = None

        try:
            p2 = next(iter2)
        except StopIteration:
            p2 = None

        # Loop through the postings as long as p1 nor p2 is None
        while p1 is not None and p2 is not None:
            # Doc_id is the same, yield one of them and advanve both iterators
            if p1.document_id == p2.document_id:
                yield p1
                try:
                    p1 = next(iter1)
                except StopIteration:
                    p1 = None # Has to set to empty, since stupid. 
                   
                try:
                    p2 = next(iter2)
                except StopIteration:
                    p2 = None 
                  
            # Advance the first list to it matches the second list
            elif p1.document_id < p2.document_id:
                yield p1
                try:
                    p1 = next(iter1)
                except StopIteration:
                    p1 = None  
            else:
                yield p2
                try:
                    p2 = next(iter2)
                except StopIteration:
                    p2 = None
                
        # Yield the posting list that is not None, set to None in while loop. (Not a fan)
        if p1 is not None:
            yield p1
            yield from iter1

        if p2 is not None:
            yield p2
            yield from iter2
      
        # raise NotImplementedError("You need to implement this as part of the obligatory assignment.")

    @staticmethod
    def difference(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple ANDNOT(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        # Check if empty
        try:
            p1 = next(iter1)
        except StopIteration:
            p1 = None
        try:
            p2 = next(iter2)
        except StopIteration:
            p2 = None
    
        while p1 is not None and p2 is not None:
            if p1.document_id == p2.document_id:

                # Trying to iterate to the next posting
                try:
                    p1 = next(iter1)
                except StopIteration:
                    p1 = None
                try:
                    p2 = next(iter2)
                except StopIteration:
                    p2 = None

            # Never intrested of yielding p2. So only yield p1 and move along. 
            elif p1.document_id < p2.document_id:
                yield p1
                try:
                    p1 = next(iter1)
                except StopIteration:
                    p1 = None
            else:
                try:
                    p2 = next(iter2)
                except StopIteration:
                    p2 = None

        # Yield the rest of the postings (for that time p2 is shorter than p1)
        if p1 is not None:
            yield p1
            yield from iter1
                        
        # raise NotImplementedError("You need to implement this as part of the obligatory assignment.")
