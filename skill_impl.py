import os
import time
import uuid
from decimal import Decimal, InvalidOperation, getcontext
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware

load_dotenv()
getcontext().prec = 40

_CHAIN_CONFIG = {
    "base-sepolia": {
        "chain_id": 84532,
        "cctp_domain": 6,
        "rpc_env": "BASE_SEPOLIA_RPC",
        "usdc_env": "BASE_SEPOLIA_USDC",
        "token_messenger_env": "BASE_SEPOLIA_TOKEN_MESSENGER",
        "message_transmitter_env": "BASE_SEPOLIA_MESSAGE_TRANSMITTER",
    },
    "arbitrum-sepolia": {
        "chain_id": 421614,
        "cctp_domain": 3,
        "rpc_env": "ARBITRUM_SEPOLIA_RPC",
        "usdc_env": "ARBITRUM_SEPOLIA_USDC",
        "token_messenger_env": "ARBITRUM_SEPOLIA_TOKEN_MESSENGER",
        "message_transmitter_env": "ARBITRUM_SEPOLIA_MESSAGE_TRANSMITTER",
    },
}

_ERC20_ABI = [
    {"name": "decimals", "type": "function", "stateMutability": "view", "inputs": [], "outputs": [{"type": "uint8"}]},
    {"name": "symbol", "type": "function", "stateMutability": "view", "inputs": [], "outputs": [{"type": "string"}]},
    {"name": "balanceOf", "type": "function", "stateMutability": "view", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"type": "uint256"}]},
    {"name": "transfer", "type": "function", "stateMutability": "nonpayable", "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}]},
    {"name": "approve", "type": "function", "stateMutability": "nonpayable", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}]},
]

_TOKEN_MESSENGER_ABI = [
    {
        "name": "depositForBurn",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "destinationDomain", "type": "uint32"},
            {"name": "mintRecipient", "type": "bytes32"},
            {"name": "burnToken", "type": "address"},
        ],
        "outputs": [{"type": "uint64"}],
    }
]

_MESSAGE_TRANSMITTER_ABI = [
    {
        "anonymous": False,
        "type": "event",
        "name": "MessageSent",
        "inputs": [{"indexed": False, "name": "message", "type": "bytes"}],
    },
    {
        "name": "receiveMessage",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "message", "type": "bytes"},
            {"name": "attestation", "type": "bytes"},
        ],
        "outputs": [{"type": "bool"}],
    },
]


def _ensure_testnet() -> None:
    if os.getenv("TESTNET", "false").lower() != "true":
        raise RuntimeError("TESTNET=true required; mainnet is blocked")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


_DEFAULT_ADDRESSES = {
    "BASE_SEPOLIA_USDC": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "ARBITRUM_SEPOLIA_USDC": "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
    "BASE_SEPOLIA_TOKEN_MESSENGER": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
    "ARBITRUM_SEPOLIA_TOKEN_MESSENGER": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
    "BASE_SEPOLIA_MESSAGE_TRANSMITTER": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
    "ARBITRUM_SEPOLIA_MESSAGE_TRANSMITTER": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
}


def _require_address_env(name: str, w3: Web3) -> str:
    value = os.getenv(name, "").strip() or _DEFAULT_ADDRESSES.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    if not w3.is_address(value):
        raise ValueError(f"Invalid address in env var: {name}")
    return w3.to_checksum_address(value)


def _get_chain_config(chain: str) -> Dict[str, Any]:
    if chain not in _CHAIN_CONFIG:
        raise ValueError(f"Unsupported chain: {chain}")
    return _CHAIN_CONFIG[chain]


def _get_web3(chain: str) -> Web3:
    config = _get_chain_config(chain)
    rpc_url = _require_env(config["rpc_env"])
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not w3.is_connected():
        raise RuntimeError(f"Failed to connect to RPC for {chain}")
    return w3


def _get_usdc_contract(w3: Web3, chain: str):
    config = _get_chain_config(chain)
    address = _require_address_env(config["usdc_env"], w3)
    return w3.eth.contract(address=address, abi=_ERC20_ABI)


def _get_token_messenger(w3: Web3, chain: str):
    config = _get_chain_config(chain)
    address = _require_address_env(config["token_messenger_env"], w3)
    return w3.eth.contract(address=address, abi=_TOKEN_MESSENGER_ABI)


def _get_message_transmitter(w3: Web3, chain: str):
    config = _get_chain_config(chain)
    address = _require_address_env(config["message_transmitter_env"], w3)
    return w3.eth.contract(address=address, abi=_MESSAGE_TRANSMITTER_ABI)


def _decimal_to_str(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _to_base_units(amount: str, decimals: int) -> int:
    try:
        dec = Decimal(amount)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount format") from exc
    if dec <= 0:
        raise ValueError("Amount must be greater than 0")
    base = Decimal(10) ** decimals
    scaled = dec * base
    if scaled != scaled.to_integral_value():
        raise ValueError(f"Amount has more than {decimals} decimal places")
    return int(scaled)


def _sign_and_send(w3: Web3, tx: Dict[str, Any], privkey: str) -> str:
    if "gas" not in tx:
        tx["gas"] = w3.eth.estimate_gas(tx)
    signed = w3.eth.account.from_key(privkey).sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.rawTransaction).hex()


def _build_tx(w3: Web3, chain: str, from_addr: str, nonce: int) -> Dict[str, Any]:
    return {
        "from": from_addr,
        "nonce": nonce,
        "chainId": _get_chain_config(chain)["chain_id"],
        "gasPrice": w3.eth.gas_price,
    }


def _wait_for_receipt(w3: Web3, txid: str, timeout: int = 180, poll_interval: int = 3):
    start = time.time()
    while time.time() - start < timeout:
        try:
            return w3.eth.get_transaction_receipt(txid)
        except TransactionNotFound:
            time.sleep(poll_interval)
    raise RuntimeError(f"Timeout waiting for receipt: {txid}")


def _message_from_receipt(w3: Web3, chain: str, receipt) -> bytes:
    message_transmitter = _get_message_transmitter(w3, chain)
    event = message_transmitter.events.MessageSent()
    for log in receipt.logs:
        try:
            decoded = event.process_log(log)
        except Exception:
            continue
        return decoded["args"]["message"]
    raise RuntimeError("CCTP MessageSent event not found in receipt")


def _attestation_for_message(message: bytes) -> str:
    base = os.getenv("CCTP_API_BASE", "https://cctp-test.circle.com").rstrip("/")
    message_hash = Web3.keccak(message).hex()
    path = f"{base}/attestations/{message_hash}"
    timeout = int(os.getenv("CCTP_ATTEST_TIMEOUT", "300"))
    poll_interval = int(os.getenv("CCTP_ATTEST_POLL", "5"))
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(path, timeout=20)
        if resp.status_code != 200:
            time.sleep(poll_interval)
            continue
        payload = resp.json()
        status = payload.get("status", "")
        attestation = payload.get("attestation")
        if status.lower() == "complete" and attestation:
            if not attestation.startswith("0x"):
                attestation = "0x" + attestation
            return attestation
        time.sleep(poll_interval)
    raise RuntimeError("Timed out waiting for CCTP attestation")


def usdc_balance(account: str, chain: str = "base-sepolia") -> Dict[str, Any]:
    _ensure_testnet()
    w3 = _get_web3(chain)
    contract = _get_usdc_contract(w3, chain)
    if not w3.is_address(account):
        raise ValueError("Invalid account address")
    acct = w3.to_checksum_address(account)
    decimals = contract.functions.decimals().call()
    raw_balance = contract.functions.balanceOf(acct).call()
    balance = Decimal(raw_balance) / (Decimal(10) ** decimals)
    return {
        "balance": _decimal_to_str(balance),
        "token": contract.functions.symbol().call(),
        "chain": chain,
        "account": acct,
    }


def usdc_transfer_testnet(
    to: str,
    amount: str,
    simulate: bool = False,
    chain: str = "base-sepolia",
) -> Dict[str, Any]:
    _ensure_testnet()
    if not Web3.is_address(to):
        raise ValueError("Invalid recipient address")
    if simulate:
        return {
            "txid": None,
            "simulated": True,
            "chain": chain,
            "to": to,
            "amount": amount,
        }

    w3 = _get_web3(chain)
    contract = _get_usdc_contract(w3, chain)
    decimals = contract.functions.decimals().call()
    amount_base = _to_base_units(amount, decimals)
    privkey = _require_env("EVM_PRIVKEY_TEST")
    account = w3.eth.account.from_key(privkey)
    to_addr = w3.to_checksum_address(to)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.transfer(to_addr, amount_base).build_transaction(
        _build_tx(w3, chain, account.address, nonce)
    )
    txid = _sign_and_send(w3, tx, privkey)
    return {
        "txid": txid,
        "simulated": False,
        "chain": chain,
        "to": to_addr,
        "amount": amount,
        "from": account.address,
    }


def usdc_cctp_bridge_testnet(
    chain_from: str,
    chain_to: str,
    amount: str,
    simulate: bool = False,
    recipient: Optional[str] = None,
) -> Dict[str, Any]:
    _ensure_testnet()
    if chain_from == chain_to:
        raise ValueError("chain_from and chain_to must be different")
    if simulate:
        return {
            "request_id": None,
            "simulated": True,
            "from": chain_from,
            "to": chain_to,
            "amount": amount,
        }
    w3_from = _get_web3(chain_from)
    w3_to = _get_web3(chain_to)
    token_from = _get_usdc_contract(w3_from, chain_from)
    messenger = _get_token_messenger(w3_from, chain_from)
    transmitter = _get_message_transmitter(w3_to, chain_to)
    decimals = token_from.functions.decimals().call()
    amount_base = _to_base_units(amount, decimals)
    privkey = _require_env("EVM_PRIVKEY_TEST")
    account = w3_from.eth.account.from_key(privkey)

    nonce = w3_from.eth.get_transaction_count(account.address)
    approve_tx = token_from.functions.approve(messenger.address, amount_base).build_transaction(
        _build_tx(w3_from, chain_from, account.address, nonce)
    )
    approve_txid = _sign_and_send(w3_from, approve_tx, privkey)
    _wait_for_receipt(w3_from, approve_txid)

    dest_domain = _get_chain_config(chain_to)["cctp_domain"]
    target = recipient or account.address
    if not Web3.is_address(target):
        raise ValueError("Invalid recipient address")
    recipient_bytes = Web3.to_bytes(hexstr=target).rjust(32, b"\x00")
    nonce = w3_from.eth.get_transaction_count(account.address)
    burn_tx = messenger.functions.depositForBurn(
        amount_base,
        dest_domain,
        recipient_bytes,
        token_from.address,
    ).build_transaction(_build_tx(w3_from, chain_from, account.address, nonce))
    burn_txid = _sign_and_send(w3_from, burn_tx, privkey)
    burn_receipt = _wait_for_receipt(w3_from, burn_txid)
    message = _message_from_receipt(w3_from, chain_from, burn_receipt)
    message_hash = Web3.keccak(message).hex()
    attestation = _attestation_for_message(message)

    w3_to_account = w3_to.eth.account.from_key(privkey)
    nonce = w3_to.eth.get_transaction_count(w3_to_account.address)
    mint_tx = transmitter.functions.receiveMessage(message, Web3.to_bytes(hexstr=attestation)).build_transaction(
        _build_tx(w3_to, chain_to, w3_to_account.address, nonce)
    )
    mint_txid = _sign_and_send(w3_to, mint_tx, privkey)
    _wait_for_receipt(w3_to, mint_txid)
    return {
        "request_id": message_hash,
        "simulated": False,
        "from": chain_from,
        "to": chain_to,
        "amount": amount,
        "recipient": target,
        "approve_txid": approve_txid,
        "burn_txid": burn_txid,
        "mint_txid": mint_txid,
    }


def usdc_cctp_attestation_status(request_id: str) -> Dict[str, Any]:
    _ensure_testnet()
    if not request_id.startswith("0x"):
        request_id = "0x" + request_id
    base = os.getenv("CCTP_API_BASE", "https://cctp-test.circle.com").rstrip("/")
    path = f"{base}/attestations/{request_id}"
    resp = requests.get(path, timeout=20)
    if resp.status_code != 200:
        return {"status": "unknown", "request_id": request_id}
    payload = resp.json()
    status = payload.get("status", "unknown").lower()
    attestation = payload.get("attestation")
    return {
        "status": status,
        "request_id": request_id,
        "attestation": attestation,
    }


def usdc_payment_status(txid: str, chain: str = "base-sepolia") -> Dict[str, Any]:
    _ensure_testnet()
    w3 = _get_web3(chain)
    try:
        receipt = w3.eth.get_transaction_receipt(txid)
    except TransactionNotFound:
        return {"status": "pending", "txid": txid}
    current_block = w3.eth.block_number
    confirmations = max(current_block - receipt.blockNumber + 1, 0)
    status = "confirmed" if receipt.status == 1 else "failed"
    return {"status": status, "confirmations": confirmations, "txid": txid, "chain": chain}


def usdc_paylink_create(amount: str, memo: str = "") -> Dict[str, Any]:
    _ensure_testnet()
    paylink_base = os.getenv("PAYLINK_BASE_URL", "https://paylink.test/").rstrip("/")
    paylink_id = uuid.uuid4().hex
    return {
        "paylink": {
            "id": paylink_id,
            "amount": amount,
            "memo": memo,
            "currency": "USDC",
            "network": "testnet",
            "url": f"{paylink_base}/{paylink_id}",
        }
    }
