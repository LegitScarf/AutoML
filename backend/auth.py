import os
import requests
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# Cache for Clerk JWKS keys
_jwks_cache = None
_jwks_last_fetched = 0
JWKS_CACHE_TTL = 3600  # Cache keys for 1 hour

def get_clerk_jwks():
    """
    Fetches the JSON Web Key Set (JWKS) from Clerk to verify RS256 tokens.
    Uses caching to avoid excessive external network calls.
    """
    global _jwks_cache, _jwks_last_fetched
    import time
    
    now = time.time()
    if _jwks_cache and (now - _jwks_last_fetched < JWKS_CACHE_TTL):
        return _jwks_cache
        
    clerk_secret = os.getenv("CLERK_SECRET_KEY")
    if not clerk_secret or clerk_secret == "your_clerk_secret_key_here":
        raise HTTPException(
            status_code=500,
            detail="CLERK_SECRET_KEY is not configured on the server."
        )
        
    url = "https://api.clerk.com/v1/jwks"
    headers = {"Authorization": f"Bearer {clerk_secret}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        _jwks_cache = res.json()
        _jwks_last_fetched = now
        return _jwks_cache
    except Exception as e:
        if _jwks_cache:
            return _jwks_cache
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Clerk public keys for signature verification: {str(e)}"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    FastAPI dependency that extracts and validates the Clerk JWT token from the Authorization header.
    Returns a dictionary containing the user's Clerk ID and subscription tier.
    """
    token = credentials.credentials
    jwks = get_clerk_jwks()
    
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header structure.")
        
    if not kid:
        raise HTTPException(status_code=401, detail="Token header missing 'kid' attribute.")
        
    # Locate the matching public key in the JWKS
    public_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            break
            
    if not public_key:
        raise HTTPException(status_code=401, detail="JWKS matching key signature not found.")
        
    try:
        # Verify and decode the token with clock skew leeway
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            leeway=60
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token payload missing subject ('sub') claim.")
            
        # Extract custom metadata tier synchronized from Stripe (defaulting to 'premium' when billing is disabled)
        ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"
        tier = payload.get("public_metadata", {}).get("tier", "premium" if not ENABLE_TRIAL_LIMITS else "free")
        
        return {"user_id": user_id, "tier": tier}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token signature has expired.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token signature: {str(e)}")
