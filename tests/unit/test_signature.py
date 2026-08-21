from swaram.providers.crypto.delta_private import generate_delta_signature


def test_generate_delta_signature():
    # Pre-calculated test case
    secret = "test_secret"
    method = "GET"
    timestamp = "1680000000"
    path = "/v2/wallet/balances"
    
    sig = generate_delta_signature(secret, method, timestamp, path)
    
    assert len(sig) == 64
    assert isinstance(sig, str)
