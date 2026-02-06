import os
import argparse
from dotenv import load_dotenv

from skill_impl import (
    usdc_balance,
    usdc_transfer_testnet,
    usdc_cctp_bridge_testnet,
    usdc_payment_status,
    usdc_paylink_create,
)

load_dotenv()

TESTNET = os.getenv("TESTNET", "false").lower() == "true"
if not TESTNET:
    raise SystemExit("Refusing to run: TESTNET must be true")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--bridge", action="store_true", help="Run real CCTP bridge flow")
    ap.add_argument("--amount", default="1.0", help="USDC amount for transfer/bridge")
    ap.add_argument("--to", default="0x000000000000000000000000000000000000dEaD")
    ap.add_argument("--recipient", default="", help="CCTP mint recipient address")
    args = ap.parse_args()

    print("[demo] usdc_balance ...")
    if args.simulate:
        print({"balance": "1000.00", "token": "USDC", "chain": "base-sepolia", "simulated": True})
    else:
        account = os.getenv("DEMO_ACCOUNT", "")
        if not account:
            raise SystemExit("Set DEMO_ACCOUNT to a testnet address for balance checks")
        print(usdc_balance(account))

    print("[demo] usdc_transfer_testnet ...")
    print(usdc_transfer_testnet(args.to, args.amount, simulate=args.simulate))

    print("[demo] usdc_cctp_bridge_testnet ...")
    if args.bridge:
        recipient = args.recipient or None
        print(usdc_cctp_bridge_testnet("base-sepolia", "arbitrum-sepolia", args.amount, simulate=args.simulate, recipient=recipient))
    else:
        print(usdc_cctp_bridge_testnet("base-sepolia", "arbitrum-sepolia", "1.0", simulate=True))

    print("[demo] usdc_payment_status ...")
    if args.simulate:
        print({"status": "confirmed", "confirmations": 12})
    else:
        txid = os.getenv("DEMO_TXID", "")
        if not txid:
            raise SystemExit("Set DEMO_TXID to a testnet tx hash for status checks")
        print(usdc_payment_status(txid))

    print("[demo] usdc_paylink_create ...")
    print(usdc_paylink_create("10.00", memo="demo"))

if __name__ == "__main__":
    main()
