---
name: openclaw-usdc-skill
version: 0.1.0
description: Testnet-only USDC flows for agents (balance, transfer, CCTP bridge, status, paylink mock)
homepage: https://github.com/Lokmali/openclaw-usdc-skill
---

# OpenClaw USDC Skill (TESTNET ONLY)

DO NOT USE MAINNET. This skill blocks mainnet by design.

## Commands

@skill.command("usdc_balance")
- args: { account: string }
- options: { chain?: "base-sepolia"|"arbitrum-sepolia" }
- returns: { balance: string, token: "USDC", chain: string }

@skill.command("usdc_transfer_testnet")
- args: { to: string, amount: string }
- options: { simulate?: boolean, chain?: "base-sepolia"|"arbitrum-sepolia" }
- returns: { txid?: string, simulated: boolean, chain: string }

@skill.command("usdc_cctp_bridge_testnet")
- args: { chain_from: string, chain_to: string, amount: string }
- options: { simulate?: boolean, recipient?: string }
- returns: { request_id?: string, simulated: boolean }

@skill.command("usdc_cctp_attestation_status")
- args: { request_id: string }
- returns: { status: string, request_id: string, attestation?: string }

@skill.command("usdc_payment_status")
- args: { txid: string }
- options: { chain?: "base-sepolia"|"arbitrum-sepolia" }
- returns: { status: "pending"|"confirmed"|"failed", confirmations?: number }

@skill.command("usdc_paylink_create")
- args: { amount: string, memo?: string }
- returns: { paylink: object }

## Environment (.env)
- TESTNET=true
- BASE_SEPOLIA_RPC=...
- ARBITRUM_SEPOLIA_RPC=...
- BASE_SEPOLIA_USDC=...
- ARBITRUM_SEPOLIA_USDC=...
- BASE_SEPOLIA_TOKEN_MESSENGER=...
- BASE_SEPOLIA_MESSAGE_TRANSMITTER=...
- ARBITRUM_SEPOLIA_TOKEN_MESSENGER=...
- ARBITRUM_SEPOLIA_MESSAGE_TRANSMITTER=...
- CCTP_API_BASE=https://cctp-test.circle.com (example)
- EVM_PRIVKEY_TEST=0x...
- PAYLINK_BASE_URL=https://paylink.test/

## Notes
- All commands enforce TESTNET=true and reject mainnet chain IDs.
- `simulate` allows dry‑run output for demos.
