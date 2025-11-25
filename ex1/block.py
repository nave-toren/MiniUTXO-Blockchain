
from .utils import BlockHash
from .transaction import Transaction
from typing import List
import hashlib


class Block:
    # implement __init__ as you see fit.
    def __init__(self, prev_hash: BlockHash, transactions:List[Transaction]) :
        self.prev_hash = prev_hash
        self.transactions = transactions

    def get_block_hash(self) -> BlockHash:  # start with the hash of the previous block (already bytes)
        """returns hash of this block"""
        data = self.prev_hash

        for tx in self.transactions: # add the txid of each transaction in this block
            data += tx.get_txid()

        return hashlib.sha256(data).digest()# compute SHA256 of the full byte sequence


    def get_transactions(self) -> List[Transaction]:
        """returns the list of transactions in this block."""

        return self.transactions


    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block in the chain"""
        return self.prev_hash
