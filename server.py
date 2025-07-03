"""
One-stop MCP server that wraps BOTH:

 • Pump Portal (SOL)→ default REST base https://api-solana.nodra.app

▶ python server.py
or
▶ uv run mcp dev server.py
"""
from typing import Dict, Any
import os
import json
import urllib.request
import urllib.parse
import mimetypes
import uuid
import contextlib
from mcp.server.fastmcp import FastMCP  # type: ignore[import] 

SOL_BASE = os.getenv("PUMP_BASE_URL", "https://api-solana.nodra.app")
TIMEOUT = int(os.getenv("MCP_HTTP_TIMEOUT", "60"))

mcp = FastMCP(
    name="Nodra Server Create, Buy, Sell Tokens",
    instruction="""
    When asked to create, buy or sell solana-based token, call sol_create_token to create a new token,
    sol_buy_token to buy an existing token,  sol_sell_token to sell an existing token, or sol_create_wallet to create a new wallet.
    """
)


def _get_json(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())

def _post_json(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    encoded = urllib.parse.urlencode({k: v for k, v in data.items() if v is not None}).encode()
    req = urllib.request.Request(url, data=encoded)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())

def _post_multipart(url: str, fields: Dict[str, Any], files: Dict[str, Any]) -> Dict[str, Any]:
    boundary = uuid.uuid4().hex
    data = b""

    for key, value in fields.items():
        if value is None:
            continue
        data += (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{key}\"\r\n\r\n"
            f"{value}\r\n"
        ).encode()

    for field, file in files.items():
        filename = os.path.basename(file.name)
        content = file.read()
        filetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        data += (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {filetype}\r\n\r\n"
        ).encode() + content + b"\r\n"

    data += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())

# MCP Tools 

@mcp.tool()
def sol_create_wallet() -> str:
    """
    **Generate a brand-new Solana wallet**.

    Returns
    -------
    str  JSON containing `apiKey`, `walletPublicKey`, and `privateKey`.
    """
    return json.dumps(_get_json(f"{SOL_BASE}/pump/createWallet"), indent=2)

@mcp.tool()
def sol_transfer_sol(fromPrivateKey: str, toPublicKey: str, amountSol: float) -> str:
    """
    **Transfer SOL** between wallets.

    Parameters
    ----------
    fromPrivateKey : str  Base-58 sender key.  
    toPublicKey    : str  Base-58 recipient address.  
    amountSol      : float SOL to send (e.g. 0.02).

    Returns
    -------
    str  JSON with the signature of the system-transfer transaction.
    """
    body = {
        "fromPrivateKey": fromPrivateKey,
        "toPublicKey": toPublicKey,
        "amountSol": amountSol
    }
    return json.dumps(_post_json(f"{SOL_BASE}/pump/transferSOL", body), indent=2)

@mcp.tool()
def sol_execute_trade(privateKeyBase58: str, publicKey: str, mint: str,
                      action: str = "buy", denominatedInSol: bool = False,
                      amount: float = 0.001, slippage: float = 10,
                      priorityFee: float = 0.00001) -> str:
    """
    **Trade an SPL token** (Pump Portal if listed, else Raydium).

    * action: `"buy"` or `"sell"`  
    * denominatedInSol=False ➜ *amount* is in TOKENs; True ➜ amount is SOL.  
    * slippage: % allowed price movement.  
    * priorityFee: extra SOL for high-priority TX.

    Returns
    -------
    str – JSON `{success, signature, explorerUrl, …}`.
    """
    body = {
        "privateKeyBase58": privateKeyBase58,
        "publicKey": publicKey,
        "mint": mint,
        "action": action,
        "denominatedInSol": denominatedInSol,
        "amount": amount,
        "slippage": slippage,
        "priorityFee": priorityFee,
    }
    return json.dumps(_post_json(f"{SOL_BASE}/pump/executeTrade", body), indent=2)

@mcp.tool()
def sol_create_token(fromPrivateKey: str, imagePath: str,
                     tokenName: str, tokenSymbol: str, tokenDescription: str,
                     devBuy: float = 0.001) -> str:
    """
    **Mint a brand-new SPL token** and host its metadata on IPFS.

    *devBuy* is the SOL amount Pump spends buying back the token on creation.
    """
    with contextlib.ExitStack() as stack:
        files = {"file": stack.enter_context(open(imagePath, "rb"))}
        body = {
            "fromPrivateKey": fromPrivateKey,
            "tokenName": tokenName,
            "tokenSymbol": tokenSymbol,
            "tokenDescription": tokenDescription,
            "devBuy": devBuy
        }
        return json.dumps(_post_multipart(f"{SOL_BASE}/pump/createToken", body, files), indent=2)


