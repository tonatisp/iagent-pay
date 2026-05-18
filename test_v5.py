import sys, os, time
from decimal import Decimal

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

results = []
passed = 0
failed = 0

def run_test(name, func):
    global passed, failed
    try:
        func()
        results.append(f"PASS {name}")
        passed += 1
    except AssertionError as e:
        results.append(f"FAIL {name}: Assertion Failed: {e}")
        failed += 1
    except Exception as e:
        results.append(f"FAIL {name}: {type(e).__name__}: {e}")
        failed += 1

print("Starting iAgentPay v5.0 Comprehensive Tests...")

# --- SAFETY KERNEL TESTS ---
def test_safety_kernel():
    from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig, BudgetExceeded, RateLimitExceeded, TransactionCapExceeded, RecipientNotAllowed
    
    # Valid check
    k = SafetyKernel(SafetyConfig(daily_limit_usd=100, session_limit_usd=50, max_tx_usd=10, max_tx_per_minute=5, enable_whitelist=False))
    assert k.check(5.0, '0xAlice') == True

    # Tx Cap
    k2 = SafetyKernel(SafetyConfig(max_tx_usd=1.0))
    try:
        k2.check(5.0, '0xBob')
        assert False, "Should have blocked tx cap"
    except TransactionCapExceeded:
        pass

    # Budget
    k3 = SafetyKernel(SafetyConfig(session_limit_usd=5.0, max_tx_usd=3.0))
    k3.check(3.0, '0xA')
    try:
        k3.check(3.0, '0xA')
        assert False, "Should have blocked budget"
    except BudgetExceeded:
        pass

    # Rate Limit
    k4 = SafetyKernel(SafetyConfig(max_tx_per_minute=2))
    k4.check(1.0, '0xA')
    k4.check(1.0, '0xA')
    try:
        k4.check(1.0, '0xA')
        assert False, "Should have blocked rate limit"
    except RateLimitExceeded:
        pass

    # Whitelist
    k5 = SafetyKernel(SafetyConfig(enable_whitelist=True, allowed_recipients=['0xTrusted']))
    try:
        k5.check(1.0, '0xBadGuy')
        assert False, "Should have blocked whitelist"
    except RecipientNotAllowed:
        pass
    assert k5.check(1.0, '0xTrusted') == True

    status = k.get_status()
    assert 'session_spent' in status

run_test("SafetyKernel: Core functionality", test_safety_kernel)

# --- KYA TESTS ---
def test_kya():
    from iagent_pay.kya import AgentIdentity, KYARegistry, TrustLevel
    
    id1 = AgentIdentity.create('TestBot', '0xOwner123', ['payments'])
    assert id1.did.startswith('did:iagent:'), "DID prefix mismatch"

    reg = KYARegistry()
    assert reg.register(id1) == True, "Registration failed"
    assert reg.get_trust_level(id1.did) == TrustLevel.BASIC, f"Initial trust should be BASIC, got {reg.get_trust_level(id1.did)}"

    for _ in range(15):
        reg.update_after_payment(id1.did, True, 20.0)
    
    assert reg.get_trust_level(id1.did).value >= TrustLevel.TRUSTED.value, f"Trust should upgrade, got {reg.get_trust_level(id1.did)}"
    assert reg.get_art_score(id1.did) > 50.0, f"ART score should increase, got {reg.get_art_score(id1.did)}"

    id2 = AgentIdentity.create('BadBot', '0xBad', [])
    reg.register(id2)
    reg.blacklist(id2.did, 'fraud')
    assert reg.get_trust_level(id2.did) == TrustLevel.BLACKLISTED, "Blacklist failed"

    cred = reg.issue_credential(id1.did, 'PaymentCapability', {'limit': 100})
    assert cred is not None and cred.is_valid(), "Credential issue failed"

    report = reg.get_full_report(id1.did)
    assert 'trust_level' in report and 'art_score' in report, "Report missing keys"

    stats = reg.get_registry_stats()
    assert stats['total_agents'] == 2, f"Expected 2 agents, got {stats['total_agents']}"

run_test("KYA: Identity and Trust", test_kya)

# --- WEBHOOKS TESTS ---
def test_webhooks():
    from iagent_pay.webhooks import WebhookManager, WebhookEvent, WEBHOOK_EVENTS
    
    assert len(WEBHOOK_EVENTS) >= 10, "Expected >=10 events"

    wm = WebhookManager(default_secret='test-secret-key')
    payload = '{"amount": 5.0}'
    sig = WebhookManager.sign(payload, 'test-secret-key')
    assert WebhookManager.verify_signature(payload, sig, 'test-secret-key') == True, "Valid sig failed"
    assert WebhookManager.verify_signature(payload, sig, 'wrong-secret') == False, "Invalid sig succeeded"
    
    tampered = '{"amount": 999.0}'
    assert WebhookManager.verify_signature(tampered, sig, 'test-secret-key') == False, "Tampered sig succeeded"

    received = []
    wm.on('payment.completed', lambda e: received.append(e))
    wm.emit('payment.completed', {'amount': 5.0, 'currency': 'USDC'}, async_delivery=False)
    time.sleep(0.1)
    assert len(received) == 1, "Local handler not fired"

    wm.register('https://httpbin.org/post', secret='abc', events=['payment.completed'])
    assert len(wm.list_endpoints()) == 1, "Register endpoint failed"
    wm.unregister('https://httpbin.org/post')
    assert len(wm.list_endpoints()) == 0, "Unregister endpoint failed"

    evt = WebhookEvent('payment.completed', {'amount': 1.0})
    d = evt.to_dict()
    assert 'id' in d and 'type' in d and 'data' in d, "Event dict missing keys"

run_test("Webhooks: Signatures and Delivery", test_webhooks)

# --- SUB AGENTS TESTS ---
def test_sub_agents():
    from iagent_pay.sub_agents import SubAgentManager
    from iagent_pay.safety_kernel import TransactionCapExceeded
    
    mgr = SubAgentManager(master_budget_usd=200.0)
    researcher = mgr.create('researcher', daily_limit_usd=30.0, max_tx_usd=5.0)
    writer = mgr.create('writer', daily_limit_usd=15.0, max_tx_usd=2.0)

    assert len(mgr.list_agents()) == 2, "Agent count mismatch"
    assert researcher.api_key.startswith('iap_sub_'), "API key format wrong"
    assert researcher.spend(2.0, 'USDC', 'data purchase') == True, "Spend active failed"

    mgr.pause('writer')
    assert writer.spend(1.0, 'USDC', 'test') == False, "Spend paused succeeded"

    mgr.resume('writer')
    assert writer.spend(1.0, 'USDC', 'test') == True, "Spend resumed failed"

    s = mgr.get_status()
    assert 'total_count' in s and s['total_count'] == 2, "Status agent count mismatch"

    researcher.kernel.check(3.0, '0xDataAPI')
    try:
        researcher.kernel.check(10.0, '0xDataAPI')
        assert False, "Should have blocked transaction cap"
    except TransactionCapExceeded:
        pass

    assert mgr.terminate('writer') == True, "Terminate failed"
    assert len(mgr.list_agents()) == 1, "Agent count after terminate mismatch"
    assert mgr.get('researcher') is not None, "Get existing failed"
    assert mgr.get('nonexistent') is None, "Get nonexistent should be None"

run_test("SubAgents: Fleet Management", test_sub_agents)

# --- OBSERVABILITY TESTS ---
def test_observability():
    from iagent_pay.observability import PaymentObserver, ObservabilityConfig, AnomalyDetector, get_observer
    
    obs = PaymentObserver(ObservabilityConfig(enable_anomaly_detection=True, anomaly_threshold_multiplier=2.0))
    for i in range(10):
        obs.record_payment(1.0, 'USDC', '0xRecipient', True)
    
    s = obs.get_stats()
    assert s['payments_success'] == 10, "Success count mismatch"
    
    obs.record_payment(0.5, 'USDC', '0xFail', False)
    assert obs.get_stats()['payments_failed'] == 1, "Failed count mismatch"
    
    rate = obs.get_stats()['success_rate']
    assert 0 < rate <= 100, "Success rate out of bounds"

    obs.record_x402('https://api.example.com/data', 0.01, True)
    assert obs.get_stats()['x402_paid'] == 1, "x402 count mismatch"

    obs.record_budget_block('Daily limit exceeded', 5.0, 'USDC')
    assert obs.get_stats()['budget_blocks'] == 1, "Budget block count mismatch"

    prom = obs.get_prometheus_metrics()
    assert 'iagentpay_payments_total' in prom and 'iagentpay_total_spent_usd' in prom, "Prometheus missing keys"

    events = obs.get_recent_events(5)
    assert isinstance(events, list), "Events not a list"

    det = AnomalyDetector(threshold_multiplier=2.0)
    for _ in range(10):
        det.check(1.0)
    anomaly = det.check(100.0)
    assert anomaly is not None and 'ANOMALY' in anomaly, "Anomaly not detected"

    no_anomaly = det.check(1.1)
    assert no_anomaly is None, "False anomaly detected"

    assert get_observer() is not None, "Global observer is None"

run_test("Observability: Metrics and Anomalies", test_observability)

# --- X402 SERVER TESTS ---
def test_x402_server():
    from iagent_pay.x402_server import _build_payment_instructions, HEADER_PAYMENT_REQUIRED
    
    instr = _build_payment_instructions('0xPayee', 0.10, 'BASE_SEPOLIA', 'Test API')
    assert instr['version'] == 'x402/1.0', "Version mismatch"
    assert instr['amount'] == 0.10, "Amount mismatch"
    assert instr['currency'] == 'USDC', "Currency mismatch"
    assert 'expires_at' in instr and instr['expires_at'] > int(instr['nonce']), "Expiry wrong"
    assert HEADER_PAYMENT_REQUIRED == 'X-Payment-Required', "Header wrong"

run_test("x402 Server: Middleware Basics", test_x402_server)

# --- X402 CLIENT TESTS ---
def test_x402_client():
    from iagent_pay.x402_client import X402Client
    
    c = X402Client(private_key='0x' + 'a'*64, max_amount_usdc=0.5)
    assert c.max_amount_usdc == 0.5, "Amount limit mismatch"
    assert c.get_payment_history() == [], "History not empty"
    assert c.get_total_spent() == Decimal('0'), "Total spent not zero"

run_test("x402 Client: Initialization", test_x402_client)

# --- USDC DRIVER TESTS ---
def test_usdc_driver():
    from iagent_pay.usdc_driver import USDCDriver, USDC_ADDRESSES
    
    assert 'BASE_MAINNET' in USDC_ADDRESSES, "Missing address"
    assert 'SOLANA_MAINNET' in USDC_ADDRESSES, "Missing address"

    d = USDCDriver(network='BASE_SEPOLIA')
    assert d.network == 'BASE_SEPOLIA', "Network mismatch"

    try:
        d2 = USDCDriver(network='ETH_MAINNET')
        d2.send('0x'+'a'*64, '0x'+'b'*40, 1.0)
        assert False, "Should raise exception for invalid network"
    except Exception:
        pass

run_test("USDC Driver: Network config", test_usdc_driver)

# --- MCP SERVER TESTS ---
def test_mcp_server():
    from iagent_pay.mcp_server import MCPServer, MCPToolHandler, MCP_TOOLS
    
    assert len(MCP_TOOLS) >= 6, "Tools count mismatch"
    tool_names = [t['name'] for t in MCP_TOOLS]
    for expected in ['pay', 'get_balance', 'swap', 'get_history', 'status', 'x402_request']:
        assert expected in tool_names, f"Tool {expected} missing"

    handler = MCPToolHandler()
    r = handler.handle('status', {})
    assert 'version' in r, "Status handler missing version"

    r2 = handler.handle('get_balance', {'currency': 'ALL'})
    assert 'balances' in r2, "Balance handler missing balances"

    r3 = handler.handle('swap', {'from_token': 'SOL', 'to_token': 'USDC', 'amount': 1.0})
    assert r3.get('from_token') == 'SOL', "Swap handler missing from_token"

    r4 = handler.handle('nonexistent_tool', {})
    assert 'error' in r4, "Unknown tool should error"

    srv = MCPServer()
    resp = srv._handle_request({'method': 'tools/list', 'id': 1, 'params': {}})
    assert 'result' in resp and 'tools' in resp['result'], "tools/list failed"

    resp2 = srv._handle_request({'method': 'initialize', 'id': 2, 'params': {}})
    assert resp2['result']['serverInfo']['name'] == 'iagentpay', "initialize failed"

    resp3 = srv._handle_request({'method': 'unknown.method', 'id': 3, 'params': {}})
    assert 'error' in resp3, "Unknown method should error"

run_test("MCP Server: Tool Handling", test_mcp_server)

# --- FIAT BRIDGE TESTS ---
def test_fiat_bridge():
    from iagent_pay.fiat_bridge import FiatBridge
    
    bridge = FiatBridge(stripe_key='')
    result = bridge.smart_send(10.0, '0x' + 'a'*40, 'test', prefer_crypto=True)
    assert result.rail == 'usdc', "Smart send crypto failed"

    try:
        result2 = bridge.smart_send(10.0, 'user@example.com', 'invoice')
        assert False, "Should require stripe key"
    except RuntimeError:
        pass

    result3 = bridge.smart_send(10.0, 'unknown_recipient')
    assert result3.status == 'unroutable', "Unroutable failed"

    try:
        bridge.send_stripe(10.0, 'acct_test')
        assert False, "Should require key"
    except RuntimeError:
        pass

run_test("Fiat Bridge: Routing and Config", test_fiat_bridge)

# --- HUMAN LOOP TESTS ---
def test_human_loop():
    from iagent_pay.human_loop import HumanApproval, HumanLoopConfig
    
    hitl = HumanApproval(HumanLoopConfig(threshold_usd=100.0, allow_console_approval=False))
    approved = hitl.request_approval(5.0, 'USDC', '0xBob', 'small payment')
    assert approved == True, "Auto approve failed"

    assert hitl.approve('nonexistent') == False, "Approve unknown should fail"
    assert hitl.reject('nonexistent') == False, "Reject unknown should fail"

    pending = hitl.list_pending()
    assert isinstance(pending, list), "List pending not list"

run_test("HumanLoop: HITL basics", test_human_loop)

# --- INTEGRATION TESTS ---
def test_integration():
    from iagent_pay.observability import PaymentObserver
    from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig, BudgetExceeded
    from iagent_pay.webhooks import WebhookManager

    obs2 = PaymentObserver()
    k6   = SafetyKernel(SafetyConfig(daily_limit_usd=50.0, session_limit_usd=50.0, max_tx_usd=50.0))
    wm2  = WebhookManager(default_secret='integration-secret')
    fired = []
    wm2.on('payment.completed', lambda e: fired.append(e))
    wm2.on('budget.exceeded',   lambda e: fired.append(e))

    for i in range(5):
        try:
            k6.check(5.0, '0xRecipient')
            obs2.record_payment(5.0, 'USDC', '0xRecipient', True)
            wm2.emit('payment.completed', {'amount': 5.0, 'tx': i}, async_delivery=False)
        except Exception as e:
            assert False, f"Unexpected exception in loop: {e}"

    s = obs2.get_stats()
    assert s['payments_success'] == 5, f"Expected 5 successes, got {s['payments_success']}"
    assert len(fired) == 5, f"Expected 5 webhooks, got {len(fired)}"

    try:
        k6.check(30.0, '0xRecipient')
        assert False, "Should have blocked budget"
    except BudgetExceeded:
        wm2.emit('budget.exceeded', {'reason': 'daily limit'}, async_delivery=False)
        obs2.record_budget_block('daily limit', 30.0, 'USDC')
        assert len(fired) == 6, f"Expected 6 webhooks, got {len(fired)}"

run_test("Integration: Kernel + Webhooks + Observability", test_integration)

# --- STRESS TESTS ---
def test_stress_safety():
    from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig
    k7 = SafetyKernel(SafetyConfig(daily_limit_usd=10000, session_limit_usd=10000, max_tx_usd=100, max_tx_per_minute=200, max_tx_per_hour=500))
    stress_pass = 0
    for i in range(100):
        try:
            k7.check(1.0, f'0xAddr{i}')
            stress_pass += 1
        except: pass
    assert stress_pass == 100

def test_stress_webhooks():
    from iagent_pay.webhooks import WebhookManager
    sig_pass = 0
    for i in range(50):
        p = f'payload_{i}'
        s = WebhookManager.sign(p, 'secret')
        if WebhookManager.verify_signature(p, s, 'secret'):
            sig_pass += 1
    assert sig_pass == 50

def test_stress_subagents():
    from iagent_pay.sub_agents import SubAgentManager
    mgr2 = SubAgentManager(master_budget_usd=999999)
    for i in range(100):
        mgr2.create(f'agent_{i}', daily_limit_usd=100)
    assert len(mgr2.list_agents()) == 100

def test_stress_observability():
    from iagent_pay.observability import PaymentObserver
    obs3 = PaymentObserver()
    for i in range(300):
        obs3.record_payment(float(i % 10 + 1), 'USDC', '0xAddr', i % 7 != 0)
    s3 = obs3.get_stats()
    assert s3['payments_total'] == 300

def test_stress_kya():
    from iagent_pay.kya import KYARegistry, AgentIdentity
    reg2 = KYARegistry()
    for i in range(50):
        aid = AgentIdentity.create(f'Bot{i}', f'0xOwner{i}')
        reg2.register(aid)
        for _ in range(20):
            reg2.update_after_payment(aid.did, True, 5.0)
    stats2 = reg2.get_registry_stats()
    assert stats2['total_agents'] == 50

run_test("Stress: 100 Rapid Safety Checks", test_stress_safety)
run_test("Stress: 50 Webhook Signatures", test_stress_webhooks)
run_test("Stress: 100 SubAgents Created", test_stress_subagents)
run_test("Stress: 300 Observability Events", test_stress_observability)
run_test("Stress: 50 KYA Agents with Reputation", test_stress_kya)


# --- PRINT RESULTS ---
print("\n" + "="*60)
print(f"  iAgentPay v5.0 TEST SUITE RESULTS")
print("="*60)
for r in results:
    icon = '[PASS]' if r.startswith('PASS') else '[FAIL]'
    print(f"  {icon} {r[5:]}")  # Remove the prefix and add our own
print("="*60)
print(f"  TOTAL:  {passed + failed} tests")
print(f"  PASSED: {passed}")
print(f"  FAILED: {failed}")
print("="*60)

if failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
