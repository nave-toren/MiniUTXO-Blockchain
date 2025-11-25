from __future__ import annotations
from .utils import *
from .transaction import Transaction
#from .bank import Bank
from typing import Optional, TYPE_CHECKING # TYPE_CHECKING ייתכן וכבר קיים

if TYPE_CHECKING:
    from .bank import Bank

class Wallet:
    def __init__(self) -> None:
        """This function generates a new wallet with a new private key."""
        self.private_key, self.public_key = gen_keys()
        self.last_block_index = 0
        self.my_outputs: list[TxID]= []
        self.frozen: set[TxID] = set()
        self.balance = 0



    def update(self, bank: Bank) -> None:
        """
        This function updates the balance allocated to this wallet by querying the bank.
        Don't read all of the bank's utxo, but rather process the blocks since the last update one at a time.
        For this exercise, there is no need to validate all transactions in the block.
        """
        for i in range(self.last_block_index, len(bank.blockchain)):
            block = bank.blockchain[i]
            for tx in block.transactions:
                if tx.output == self.public_key: ##got new coin
                    self.my_outputs=[tx.get_txid()]
                    self.balance += 1

                if tx.input in self.my_outputs: ##my coin accepted
                    self.my_outputs.remove(tx.input)
                    self.balance -= 1

                if tx.input in self.frozen: ##
                    self.frozen.remove(tx.input)

        self.last_block_index=len(bank.blockchain)



    def create_transaction(self, target: PublicKey) -> Optional[Transaction]:
        """
        This function returns a signed transaction that moves an unspent coin to the target.
        It chooses the coin based on the unspent coins that this wallet had since the last update.
        If the wallet already spent a specific coin, but that transaction wasn't confirmed by the
        bank just yet (it still wasn't included in a block) then the wallet  should'nt spend it again
        until unfreeze_all() is called. The method returns None if there are no unspent outputs that can be used.
        """
        if not self.my_outputs:
            return None
        coin_to_spend = self.my_outputs[0]

        if coin_to_spend in self.frozen:
            return None

        message = target + coin_to_spend

        signature = sign(message , self.private_key)

        tx = Transaction(
            output=target,
            input=coin_to_spend,
            signature=signature
        )
        self.frozen.add(coin_to_spend) ##adding this coin to frozen, till it verify by the bank

        return tx

    def unfreeze_all(self) -> None:
        """
        Allows the wallet to try to re-spend outputs that it created transactions for (unless these outputs made it into the blockchain).
        """
        self.frozen.clear()

    def get_balance(self) -> int:
        """
        This function returns the number of coins that this wallet has.
        It will return the balance according to information gained when update() was last called.
        Coins that the wallet owned and sent away will still be considered as part of the balance until the spending
        transaction is in the blockchain.
        """
        return self.balance


        raise NotImplementedError()

    def get_address(self) -> PublicKey:
        """
        This function returns the public address of this wallet (see the utils module for generating keys).
        """
        return self.public_key
