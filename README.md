# openclaw-usdc-skill (TESTNET ONLY)

OpenClaw skill for agent-native USDC flows on testnets. Safe-by-default, great DX, and hackathon‑ready.

DO NOT USE MAINNET. Testnet only per hackathon rules.

## Features
- usdc_balance(account)
- usdc_transfer_testnet(to, amount)
- usdc_cctp_bridge_testnet(chain_from, chain_to, amount)
- usdc_payment_status(txid)
- usdc_paylink_create(amount, memo) [mock]

## Safety
- Hardcoded testnet chain IDs only
- Refuses to run if any mainnet flag is detected
- No private keys in repo; use .env with test keys ONLY

## Install
- Python 3.10+
- `pip install -r requirements.txt`
- Create `.env` and fill test values

## Environment
- `TESTNET=true`
- `BASE_SEPOLIA_RPC`, `ARBITRUM_SEPOLIA_RPC`
- `BASE_SEPOLIA_USDC`, `ARBITRUM_SEPOLIA_USDC`
- `BASE_SEPOLIA_TOKEN_MESSENGER`, `BASE_SEPOLIA_MESSAGE_TRANSMITTER`
- `ARBITRUM_SEPOLIA_TOKEN_MESSENGER`, `ARBITRUM_SEPOLIA_MESSAGE_TRANSMITTER`
- `EVM_PRIVKEY_TEST` (for transfers)
- `DEMO_ACCOUNT`, `DEMO_TXID` (demo helpers)
- `CCTP_API_BASE` (defaults to https://cctp-test.circle.com)
- `CCTP_ATTEST_TIMEOUT`, `CCTP_ATTEST_POLL` (optional)

## Run demo (dry‑run)
```bash
python scripts/demo.py --simulate
```

## Run demo (real testnet calls)
```bash
python scripts/demo.py
```

## Run demo (real CCTP bridge)
```bash
python scripts/demo.py --bridge
```

## Tips
- Default Base/Arbitrum Sepolia USDC + CCTP addresses are built in, but you can override via `.env`.
- You can customize amounts and recipients: `python scripts/demo.py --bridge --amount 2.5 --recipient 0x...`

## OpenClaw Commands
See SKILL.md for command payloads and examples.
