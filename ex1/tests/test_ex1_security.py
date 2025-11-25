from ex1 import *
import pytest
import secrets


# ההנחה: כל ה-fixtures הנדרשים (bank, alice, bob, alice_coin, charlie)
# מיובאים אוטומטית מ-conftest.py


## 🛡️ בדיקות תוקף (מניפולציה על עסקאות קיימות)

def test_attacker_changes_output_to_self(bank: Bank, alice: Wallet, bob: Wallet, charlie: Wallet,
                                         alice_coin: Transaction) -> None:
    """
    תרחיש: התוקף (Charlie) מנסה לשנות עסקה חוקית מ-Alice ל-Bob,
    כדי שהכסף יגיע אליו, תוך שימוש בחתימה המקורית.
    """
    alice.update(bank)

    # 1. Alice יוצרת עסקה חוקית ל-Bob
    tx_alice_to_bob = alice.create_transaction(bob.get_address())
    assert tx_alice_to_bob is not None

    # 2. התוקף (Charlie) משכפל את העסקה אך משנה את הפלט לכתובת שלו
    tx_stolen = Transaction(
        output=charlie.get_address(),
        input=tx_alice_to_bob.input,
        signature=tx_alice_to_bob.signature
    )

    # 3. הבנק אמור לדחות את העסקה הגנובה, כיוון שהחתימה אינה תואמת לפלט החדש
    assert not bank.add_transaction_to_mempool(tx_stolen), "הבנק צריך לדחות עסקה עם פלט שונה וחתימה ישנה"

    # 4. הבנק אמור לקבל את העסקה המקורית והחוקית
    assert bank.add_transaction_to_mempool(tx_alice_to_bob)

    bank.end_day()
    alice.update(bank)
    bob.update(bank)
    charlie.update(bank)

    assert alice.get_balance() == 0
    assert bob.get_balance() == 1
    assert charlie.get_balance() == 0


def test_attacker_changes_input_coin(bank: Bank, alice: Wallet, bob: Wallet) -> None:
    """
    תרחיש: Alice שולחת מטבע אחד, ואז מקבלת מטבע שני.
    הבדיקה מוודאת שאם Alice מנסה לשלוח את המטבע השני
    עם חתימה שנוצרה עבור המטבע הראשון, זה נכשל.
    """
    # 0. ניקוי והכנה:
    alice.update(bank)
    alice.unfreeze_all()  # שחרור המטבע הקפוא מה-Fixture (אם קפוא)

    # 1. Alice שולחת את מטבע 1 ל-Bob
    tx_coin1 = alice.create_transaction(bob.get_address())
    assert tx_coin1 is not None
    bank.add_transaction_to_mempool(tx_coin1)
    bank.end_day()  # מטבע 1 עכשיו בוזבז בבלוקצ'יין

    # 2. Alice מקבלת מטבע 2 לעצמה (זהו המטבע היחיד שיש לה כרגע)
    bank.create_money(alice.get_address())
    bank.end_day()
    alice.update(bank)  # מעכשיו, my_outputs מכיל רק את מטבע 2

    # 3. נשאר רק מטבע אחד של Alice ב-UTXO (מטבע 2)
    utxos = bank.get_utxo()
    assert len(utxos) == 1
    coin2 = utxos[0]

    # 4. Alice יוצרת עסקה חוקית ל-Bob תוך שימוש במטבע 2
    alice.unfreeze_all()  # משחרר את המטבע הזה כדי שיוכל ליצור עסקה חדשה
    tx_coin2_valid = alice.create_transaction(bob.get_address())
    assert tx_coin2_valid is not None

    # 5. התוקף יוצר עסקה חדשה עם החתימה של tx_coin2_valid,
    # אבל משתמש ב-TxID של מטבע 1 (שכבר בוזבז) כקלט.
    tx_stolen = Transaction(
        output=tx_coin2_valid.output,
        # משתמשים ב-TxID של מטבע 1 (שבוזבז) כקלט:
        input=tx_coin1.input,
        signature=tx_coin2_valid.signature
    )

    # 6. הבנק אמור לדחות את העסקה הגנובה
    assert not bank.add_transaction_to_mempool(tx_stolen), "הבנק צריך לדחות עסקה עם קלט שונה וחתימה ישנה"

    # 7. הבנק מקבל את העסקה המקורית (מטבע 2)
    assert bank.add_transaction_to_mempool(tx_coin2_valid)
    bank.end_day()
    alice.update(bank)
    bob.update(bank)

    assert alice.get_balance() == 0
    assert bob.get_balance() == 1


## 💰 בדיקת יצירת כסף (Money Creation)

def test_user_cannot_create_money(bank: Bank, bob: Wallet) -> None:
    """
    תרחיש: משתמש רגיל (Bob) מנסה ליצור עסקה עם input=None (כסף יש מאין).
    """
    # 1. Bob מנסה ליצור עסקה ללא קלט (input=None)

    # יוצר עסקה דומה ליצירת כסף, אבל חותם עליה כרגיל
    signature = sign(bob.get_address() + b'\x00', bob.private_key)

    tx_bad_creation = Transaction(
        output=bob.get_address(),
        input=None,
        signature=signature
    )

    # 2. הבנק אמור לדחות כל ניסיון של משתמש רגיל ליצור כסף (סעיף iv ב-add_transaction_to_mempool)
    assert not bank.add_transaction_to_mempool(tx_bad_creation), "משתמש רגיל לא יכול ליצור כסף (input=None)"

    # ודא שבדיקה נכשלת גם אם ה-signature לא חוקי
    tx_bad_creation_no_sig = Transaction(
        output=bob.get_address(),
        input=None,
        signature=secrets.token_bytes(48)  # חתימה רנדומלית, כמו שהבנק עושה
    )
    assert not bank.add_transaction_to_mempool(tx_bad_creation_no_sig), "הבנק אמור לדחות יצירת כסף שאינה באה ממנו"


## 🔄 בדיקות הוצאה כפולה - מניפולציה על הממפול

def test_double_spend_in_mempool_rejected(bank: Bank, alice: Wallet, bob: Wallet, charlie: Wallet,
                                          alice_coin: Transaction) -> None:
    """
    תרחיש: Alice מנסה להוציא את אותו מטבע לשני אנשים שונים, בטרם אושר הבלוק הראשון.
    """
    alice.update(bank)  # מעדכן את הארנק כך שיכיל את המטבע

    # 1. Alice שולחת מטבע 1 ל-Bob (tx1)
    tx1 = alice.create_transaction(bob.get_address())
    assert tx1 is not None

    # 2. Alice מנסה לשלוח את אותו מטבע 1 ל-Charlie (tx2)
    # היא צריכה unfreeze קודם כדי ליצור עסקה חדשה מאותו מטבע
    alice.unfreeze_all()
    tx2 = alice.create_transaction(charlie.get_address())
    assert tx2 is not None

    # 3. הבנק מקבל את העסקה הראשונה
    assert bank.add_transaction_to_mempool(tx1)

    # 4. הבנק דוחה את העסקה השנייה (סעיף iii ב-add_transaction_to_mempool)
    assert not bank.add_transaction_to_mempool(tx2), "הבנק צריך לדחות הוצאה כפולה בממפול"

    # 5. רק העסקה הראשונה נכנסת לבלוק
    bank.end_day()
    alice.update(bank)
    bob.update(bank)
    charlie.update(bank)

    assert bob.get_balance() == 1
    assert charlie.get_balance() == 0