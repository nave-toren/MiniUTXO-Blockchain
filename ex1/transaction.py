from .utils import PublicKey, TxID, Signature
from typing import Optional
import hashlib


class Transaction:
    """Represents a transaction that moves a single coin
    A transaction with no source creates money. It will only be created by the bank."""

    def __init__(self, output: PublicKey, input: Optional[TxID], signature: Signature) -> None:
        # do not change the name of this field:
        self.output: PublicKey = output
        # do not change the name of this field:
        self.input: Optional[TxID] = input
        # do not change the name of this field:
        self.signature: Signature = signature

        if self.input is None:
            input_bytes = b'\x00'   # no input → new money
        else:
            input_bytes = self.input

        to_hash = self.output + input_bytes + self.signature ##cause inpote can be none, we need to '_bytes' him
        self.txid = hashlib.sha256(to_hash).digest() ##



    def get_txid(self) -> TxID:
        """Returns the identifier of this transaction. This is the SHA256 of the transaction contents."""
        return self.txid


    def __eq__(self, other: object) -> bool:
        """Two transactions are equal if they have the same output, input and signature"""
        if not isinstance(other, Transaction):
            return False
        return self.output == other.output and self.input == other.input and self.signature == other.signature
