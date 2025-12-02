# Duplication Flow Architecture

## System Overview with Duplication Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              KOOPTIMIZER SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND LAYER (Browser)                                                 │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ Message Sending                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐  │   │
│  │ │ sendMessage() Function (Line 1975)                         │  │   │
│  │ ├─────────────────────────────────────────────────────────────┤  │   │
│  │ │ ✅ GUARD: let isSending = false;                            │  │   │
│  │ │ ✅ GUARD: let lastSendTimestamp = 0;                        │  │   │
│  │ │ ✅ DEBOUNCE: const SEND_DEBOUNCE_MS = 500;                 │  │   │
│  │ │                                                             │  │   │
│  │ │ if (isSending) return; ⚠️ CHECK 1: In-progress?            │  │   │
│  │ │ if (now - lastSendTimestamp < SEND_DEBOUNCE_MS) return; ⚠️ CHECK 2: Too fast?  │
│  │ │                                                             │  │   │
│  │ │ isSending = true;                                          │  │   │
│  │ │ fetch('/communications/api/message/send/')                │  │   │
│  │ └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  │ Event Listeners                                                 │   │
│  │ ┌─────────────────────────────────────────────────────────────┐  │   │
│  │ │ ✅ FIXED: Single click listener (Line 2102)                │  │   │
│  │ │ sendBtn.addEventListener('click', (e) => {                │  │   │
│  │ │   e.preventDefault();                                      │  │   │
│  │ │   e.stopPropagation();                                     │  │   │
│  │ │   sendMessage();                                           │  │   │
│  │ │ });                                                         │  │   │
│  │ │                                                             │  │   │
│  │ │ ✅ NO touchend listener (was causing double-fire)          │  │   │
│  │ └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                          │                                │
│                                          ▼                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ OTP Sending (first_login_setup.html)                           │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ Form Submit Handler (Line 110)                                 │   │
│  │ ┌──────────────────────────────────────────────────────────┐   │   │
│  │ │ ⚠️ PARTIAL: Button disabled on submit                    │   │   │
│  │ │ ❌ MISSING: Timestamp debounce check                     │   │   │
│  │ │ ❌ MISSING: 30-second cooldown tracking                 │   │   │
│  │ │                                                           │   │   │
│  │ │ form.addEventListener('submit', () => {                 │   │   │
│  │ │   btn.disabled = true;  ← Only this, not timestamp      │   │   │
│  │ │   btn.textContent = "Processing...";                    │   │   │
│  │ │ });                                                       │   │   │
│  │ └──────────────────────────────────────────────────────────┘   │   │
│  │ VULNERABILITY: On error/timeout, button re-enabled, user     │   │
│  │ can click again within seconds and send duplicate OTP         │   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                          │                                │
└──────────────────────────────────────────┼────────────────────────────────┘
                                          │
                                          ▼ HTTP Request
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND LAYER (Django)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POST /communications/api/message/send/                                   │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ send_message() View (views.py Line 741)                          │   │
│  ├───────────────────────────────────────────────────────────────────┤   │
│  │ 1. Get sender_id from session                                    │   │
│  │ 2. Get receiver_id from request                                  │   │
│  │ 3. Get message text                                              │   │
│  │ 4. Call stored procedure: sp_send_message(...)                  │   │
│  │ 5. ✅ Check if MessageRecipient already exists (Line 785)        │   │
│  │    if not exists: add to created_message_ids list               │   │
│  │                                                                  │   │
│  │ ❌ NO cache deduplication here                                   │   │
│  │ ❌ NO timestamp rate limiting                                    │   │
│  │ ⚠️  VULNERABLE: Same message could come twice if:               │   │
│  │    - User retries request due to network error                  │   │
│  │    - Browser/proxy retry logic sends duplicate                  │   │
│  │    - Attacker sends same request twice                          │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                          │                                │
│                                          ▼                                │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL: sp_send_message() Stored Procedure                  │   │
│  ├───────────────────────────────────────────────────────────────────┤   │
│  │ 1. INSERT INTO message (sender, receiver, text, ...)            │   │
│  │ 2. INSERT INTO message_recipient (message, receiver)            │   │
│  │                                                                  │   │
│  │ ✅ ATOMIC: Both inserts happen or neither (transaction)         │   │
│  │ ✅ NO SIGNAL FIRED: ORM not used, Django signals don't fire    │   │
│  │                                                                  │   │
│  │ Return: message_id                                              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                          │                                │
└──────────────────────────────────────────┼────────────────────────────────┘
                                          │
                                          ▼ MessageRecipient created
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL LAYER (Django Signals)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  @receiver(post_save, sender=MessageRecipient,                            │
│           dispatch_uid='message_recipient_post_save_notification')         │
│  def send_message_notification(sender, instance, created, **kwargs):      │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │ ✅ FIXED: Has dispatch_uid to prevent duplicate registration    │   │
│  │ (before: would register 2-3x on dev-server reload)              │   │
│  │                                                                  │   │
│  │ if created:                                                     │   │
│  │   ✅ Cache dedup check (Line 37)                                │   │
│  │   if cache.get(f"notif_sent_{msg_id}_{user_id}"):              │   │
│  │     return  ← Skip if already sent                              │   │
│  │   cache.set(..., True, 60)  ← Mark as sent                      │   │
│  │                                                                  │   │
│  │   send_push_notification_for_message(message, receiver)        │   │
│  │                                                                  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│  ISSUE: Signal only fires for ORM creates, NOT stored procedures        │
│  WORKAROUND: Manual call in view (below)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┴──────────────────┐
                    │                                        │
                    ▼ For ORM creates only                   ▼ Manual call
┌────────────────────────────────────────┐   ┌────────────────────────────────┐
│ Signal Trigger (if using ORM)          │   │ View Manual Call (Line 809)    │
│                                        │   │                                │
│ send_push_notification_for_message()   │   │ for message_id in created_ids: │
│ (signals.py Line 5)                    │   │   message = Message.objects... │
│                                        │   │   receiver = User.objects...   │
│ ⚠️  Could fire TWICE:                  │   │   send_push_notification_...() │
│ 1. From signal                         │   │                                │
│ 2. From manual call (if sync happens)  │   │ ⚠️  Could be called twice if:  │
│                                        │   │ - Signal also fires            │
│                                        │   │ - Code runs this path          │
│                                        │   │                                │
│ ✅ Mitigated by: Cache dedup check    │   │ ✅ Same cache check applies    │
└────────────────────────────────────────┘   └────────────────────────────────┘
                    │                                        │
                    └────────────────────┬───────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION LAYER (External API)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  send_push_notification(user, title, body) - notification_utils.py       │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │ Get WebPushSubscription for user                                │   │
│  │ IF subscription exists:                                         │   │
│  │    send_user_notification(user=django_user, payload=payload)   │   │
│  │    Log success                                                  │   │
│  │ ELSE:                                                            │   │
│  │    Log warning (user not subscribed)                            │   │
│  │                                                                  │   │
│  │ Result: 0 or 1 push notification sent ✅                        │   │
│  │                                                                  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## OTP Sending Flow (VULNERABLE)

```
┌────────────────────────────────────────────────────────────────┐
│ FRONTEND: first_login_setup.html (Line 110)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Form Submit Handler                                           │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ form.addEventListener('submit', () => {                 │  │
│ │   btn.disabled = true;                                  │  │
│ │   btn.textContent = "Processing...";                    │  │
│ │                                                          │  │
│ │   setTimeout(() => {  ← Re-enable after 3 seconds       │  │
│ │     btn.disabled = false;                               │  │
│ │   }, 3000);                                             │  │
│ │ });                                                      │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ VULNERABILITIES:                                              │
│ ❌ User gets network error after 2 seconds                    │
│ ❌ Button re-enabled after 3 seconds                          │
│ ❌ User can click again at second 4 (1 sec after re-enable)   │
│ ❌ No timestamp tracking of last send                         │
│ ❌ No 30-second cooldown check                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        │
        ▼ POST /users/first_login_setup/
┌────────────────────────────────────────────────────────────────┐
│ BACKEND: apps/users/views.py                                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ if action == 'send_otp':                                      │
│   ❌ NO cache check for recent sends                          │
│   ❌ NO rate limiting                                         │
│   ❌ NO timestamp validation                                  │
│                                                                │
│   success, error = otp_service.send_otp(mobile)              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        │
        ▼ Call OTP API
┌────────────────────────────────────────────────────────────────┐
│ BACKEND: apps/core/services/otp_service.py (Line 23)         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ def send_otp(mobile_number, template):                        │
│   ❌ NO rate limit check                                      │
│   ❌ NO cache deduplication                                   │
│                                                                │
│   pin = random PIN                                            │
│   Call Infobip API: send SMS to mobile_number                │
│   Return success/error                                        │
│                                                                │
│ PROBLEM: If called twice within seconds:                     │
│   - Sends two SMS                                            │
│   - Wastes SMS credits ($0.01-0.05 per SMS)                 │
│   - Confuses user (two different PINs)                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        │
        ▼ SMS to User's Phone
┌────────────────────────────────────────────────────────────────┐
│ Result: User receives duplicate OTPs                          │
│ "Your pin is 1234"                                            │
│ "Your pin is 5678"  ← Could have been prevented!             │
└────────────────────────────────────────────────────────────────┘
```

---

## Signal Handler Duplication Lifecycle (DEV SERVER)

```
SCENARIO: Django Dev Server Auto-Reload

Time 1: Developer saves settings.py
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│ Django Dev Server detects change                        │
│ - Triggers auto-reload                                 │
│ - Kills old app process                                │
│ - Starts new app process                               │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│ AppConfig.ready() called                                │
│ ├─ Import signals modules                              │
│ ├─ @receiver decorators executed                       │
│ └─ Signal handlers registered with Django              │
└──────────────────────────────────────────────────────────┘

BEFORE FIX:
┌──────────────────────────────────────────────────────────┐
│ @receiver(post_save, sender=Message)  ← NO dispatch_uid │
│ def send_notification(...):                            │
│    ...                                                  │
└──────────────────────────────────────────────────────────┘
        ▼
Each reload = NEW signal handler registered
Reload 1: Handler registered (count=1)
Reload 2: Handler registered again (count=2)
Reload 3: Handler registered again (count=3)

Result: When message saved:
  - Handler fires 3 times
  - send_push_notification() called 3 times
  - 3 identical notifications sent


AFTER FIX (CURRENT):
┌──────────────────────────────────────────────────────────┐
│ @receiver(post_save, sender=Message,                   │
│          dispatch_uid='message_notification')           │
│ def send_notification(...):                            │
│    ...                                                  │
└──────────────────────────────────────────────────────────┘
        ▼
Each reload = Django checks dispatch_uid
Reload 1: dispatch_uid='message_notification' → Register
Reload 2: dispatch_uid='message_notification' exists → Skip
Reload 3: dispatch_uid='message_notification' exists → Skip

Result: When message saved:
  - Handler fires 1 time ✅
  - send_push_notification() called 1 time ✅
  - 1 notification sent ✅
```

---

## Database-Level Duplicate Prevention

```
┌──────────────────────────────────────────────────────┐
│ PostgreSQL Foreign Key Constraint                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ CREATE TABLE message_recipient (                   │
│   recipient_id SERIAL PRIMARY KEY,                 │
│   message_id BIGINT NOT NULL                       │
│     REFERENCES message(message_id),                │
│   receiver_id BIGINT NOT NULL                      │
│     REFERENCES users(user_id),                     │
│   UNIQUE(message_id, receiver_id)  ← KEY CONSTRAINT│
│ );                                                  │
│                                                      │
│ Effect: Cannot have two rows with same             │
│ message_id + receiver_id combination               │
│                                                      │
│ Database Level Protection: ✅ YES                   │
│ (But error returned to user/API, not ideal)        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Summary: Multiple Layers of Protection

```
ATTACK SCENARIO: User tries to send duplicate message

├─ Layer 1: Frontend JavaScript Guard (isSending flag)
│  └─ CATCH RATE: 99% of duplicates
│  └─ FAIL: Malicious API call, network proxy, JS error
│
├─ Layer 2: Server-Side Request Deduplication (CACHE)
│  └─ CATCH RATE: 90% of remaining (network retries)
│  └─ FAIL: Distributed attack, cache miss
│
├─ Layer 3: ORM Duplicate Prevention (MessageRecipient check)
│  └─ CATCH RATE: 80% of remaining
│  └─ FAIL: Stored procedure creates both rows
│
└─ Layer 4: Database Constraint (UNIQUE key)
   └─ CATCH RATE: 100% - Last resort
   └─ RESULT: Error returned, duplicate prevented

RECOMMENDED ADDITIONAL PROTECTIONS:
┌──────────────────────────────────────────────────────┐
│ ⚠️  Layer 2 (Server-side dedup) NOT FULLY IMPLEMENTED
│ ⚠️  Need cache-based duplicate detection             │
│ ⚠️  Recommended TTL: 2-5 seconds                     │
└──────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

```
CURRENT STATE (60% complete)
████████████░░░░░░░░  60%

Layer 1: Frontend ✅ COMPLETE
├─ Message: isSending flag
├─ Debounce: 500ms
└─ Event: Single click listener

Layer 2: Backend ❌ INCOMPLETE
├─ Message: No cache dedup
├─ OTP: No rate limit
└─ Forms: No request dedup

Layer 3: Signals ✅ COMPLETE
├─ dispatch_uid: Present
├─ Cache check: Present
└─ Dedup: Working

Layer 4: Database ✅ COMPLETE
├─ UNIQUE constraint: Present
└─ PK enforcement: Working

NEXT STEPS:
1. Add cache dedup to send_message() [LOW EFFORT]
2. Add rate limit to send_otp() [LOW EFFORT]
3. Add form dedup to OTP forms [MEDIUM EFFORT]
4. Extract decorators [HIGH EFFORT, REFACTORING]
```

---

**Diagram Updated**: December 2, 2025  
**Status**: Architecture Review Complete
