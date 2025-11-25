from . import GENESIS_BLOCK_PREV
from .utils import verify
from .wallet import Wallet
from .utils import BlockHash, PublicKey
from .transaction import Transaction
from .block import Block
from typing import List
import secrets


class Bank:
    def __init__(self) -> None:
        """Creates a bank with an empty blockchain and an empty mempool."""
        self.blockchain = []
        self.mempool = []

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """
        This function inserts the given transaction to the mempool.
        It will return False iff one of the following conditions hold:
        (i) the transaction is invalid (the signature fails)
        (ii) the source doesn't have the coin that he tries to spend
        (iii) there is contradicting tx in the mempool.
        (iv) there is no input (i.e., this is an attempt to create money from nothing)
        """

        if transaction.input is None:  # (iv) reject money creation
            return False

        for tx in self.mempool:  # (iii) checking if the cuurent transaction already in bank mempool
            if tx.input == transaction.input:
                return False

        source_tx = None  # (ii) find the source transaction
        for block in self.blockchain:
            for tx in block.get_transactions():
                if tx.txid == transaction.input:
                    source_tx = tx
                    break
            if source_tx:
                break

        # no such coin exists
        if source_tx is None:
            return False

        for block in self.blockchain:  # check if the coin was spent already
            for tx in block.get_transactions():
                if tx.input == transaction.input:
                    return False  # double spend

        # (i) verify signature

        # build message like in Transaction constructor
        message = transaction.output + transaction.input

        # public key of sender is output of source transaction
        sender_public_key = source_tx.output

        if not verify(message, transaction.signature, sender_public_key):
            return False

        # PASSED ALL CHECKS → ADD
        self.mempool.append(transaction)
        return True

    def end_day(self, limit: int = 10) -> BlockHash:
        """
        This function tells the bank that the day ended,
        and that the first `limit` transactions in the mempool should be committed to the blockchain.
        If there are fewer than 'limit' transactions in the mempool, a smaller block is created.
        If there are no transactions, an empty block is created. The hash of the block is returned.
        """
        to_take = min(limit, len(self.mempool))
        transactions = self.mempool[:to_take]  # slice the first (to_take) transaction
        self.mempool = self.mempool[to_take:]  ##returning transaction without the slice number of transaction

        if len(self.blockchain) == 0:
            prev_hash = GENESIS_BLOCK_PREV
        else:
            prev_hash = self.blockchain[-1].get_block_hash()

        new_block = Block(prev_hash, transactions)  # create new block
        self.blockchain.append(new_block)
        return new_block.get_block_hash()


    def get_block(self, block_hash: BlockHash) -> Block:
        """
        This function returns a block object given its hash. If the block doesnt exist, an exception is thrown..
        """
        for block in self.blockchain:
             if block.get_block_hash() == block_hash:
                return block

        raise Exception("The block doesn't exist")


    def get_latest_hash(self) -> BlockHash:
        """
        This function returns the hash of the last Block that was created by the bank.
        """
        return self.blockchain[-1].get_block_hash()


    def get_mempool(self) -> List[Transaction]:
        """
        This function returns the list of transactions that didn't enter any block yet.
        """
        return self.mempool


    def get_utxo(self) -> List[Transaction]:
        """
        This function returns the list of unspent transactions.
        """
        all_outputs = []
        all_inputs = []

        for block in self.blockchain:
            for tx in block.get_transactions():
                all_outputs.append(tx)
                if tx.input is not None:
                    all_inputs.append(tx.input)

        utxo = [tx for tx in all_outputs if tx.get_txid() not in all_inputs]
        return utxo

    def create_money(self, target: PublicKey) -> None:
        """
        This function inserts a transaction into the mempool that creates a single coin out of thin air.
        Instead of a signature, this transaction includes a random string of 48 bytes (so that every two
        creation transactions are different). Only the bank can use this function.
        """

        signature = secrets.token_bytes(48)
        tx = Transaction(output=target, input=None, signature=signature)
        self.mempool.append(tx)