# What a real label corpus does to the escalation word lists

Research ticket: [#26](https://github.com/mohmaedeslam00116/AndroidUse/issues/26).
Date: 2026-10-22.

The device-side code under test is
`protocol/src/main/kotlin/ai/androiduse/protocol/CapabilityResolver.kt:38-85`.
It resolves the *effective capability* of a press by looking at the text and
content description of the tapped element and asking whether either of them
**contains** one of the words in `sendWords` or `paymentWords`:

```kotlin
val targetLabels: List<String>
    get() = listOfNotNull(targetText, targetDescription).map { it.lowercase() }
...
if (labels.any { label -> paymentWords.any { label.contains(it) } }) return Capability.PAYMENT_AUTHORIZE
if (labels.any { label -> sendWords.any { label.contains(it) } }) return Capability.MESSAGE_SEND
```

ADR-0003 (`docs/adr/0003-capability-based-approval.md:145-151`) already names
this as an open problem: *"They will produce false positives (a button that
happens to contain the word 'ok') and false negatives (a Send button labelled
with an icon, which has no text at all)."* This note measures how big those
two problems actually are.

**Answer in one line.** The lists are a bad detector. Under the shipped
substring rule, `تم` alone escalates **4 645** of the 82 326 distinct real
labels in the corpus to `MESSAGE_SEND` (1 851 of them even with whole-word
matching), and of the 20 ASCII entries the median plausible-positive ratio is
**0.20** - one label in five is a real hit. Four entries (`إرسل`, `order now`,
`ادفع`, `اشتري`) never fire on anything, and three of the real button
captions that matter (`forward`, `reply`, `check out`) are not in the lists at
all. The recommendation is to **replace** the two substring lists with a
**normalised, word-boundary-aware matcher over a much smaller, curated
concept set**, and to **additionally** key on the *action context* (a
`ACTION_SEND` intent, a `WebView` URL, a `role=button` node inside a
composer) rather than on the word alone.

---

## 1. The corpus

`docs/research/label-corpus.txt` is the corpus. It is plain UTF-8 text, one
label per line, `label <TAB> source_id <TAB> resource_name`, with a `##`
comment header recording the source and the extraction recipe. The extraction
tools are committed under `docs/research/tools/` so the corpus can be rebuilt
and challenged.

| | |
| --- | --- |
| rows (label, source, resource) | 151 226 |
| **distinct labels** | **82 326** |
| distinct "short" labels (≤ 4 words and ≤ 40 chars) | 49 121 |
| distinct labels containing Arabic script | 30 048 |
| distinct labels that are Arabic-only | 22 180 |
| distinct labels mixing Arabic and Latin (format specifiers removed) | 7 885 |
| distinct labels containing a bidi control character | 15 985 (4 284 Arabic) |
| APKs extracted from the image | 123 |
| APKs that declare at least one `string` resource | 108 |
| SDK platform resource tables | 7 API levels (29-36) × 2 buckets (`values`, `values-ar`) |

Provenance breakdown by source:

| source | rows | what it is |
| --- | --- | --- |
| `apk:product/...` | 78 543 | `product` partition: Gmail, Maps, YouTube, Photos, Drive, Chrome, Calendar, Dialer, Contacts, Velvet, Wellbeing, **PrebuiltGmsCore** (Play Services, incl. Play Billing and Google Pay strings), Setup Wizard, Gboard, Desk Clock |
| `apk:system_ext/...` | 24 456 | `system_ext` partition: **Settings**, **SystemUIGoogle**, Nexus Launcher, StorageManager, GoogleServicesFramework, WallpaperPicker |
| `apk:system/...` | 17 943 | `system` partition: **framework-res.apk**, DocumentsUI, Mms, Telecom, TeleService, Shell, PackageInstaller, and the rest of AOSP |
| `sdk:android-29..36` | 34 284 | the SDK platform's own `values/strings.xml` and `values-ar/strings.xml` |

The single source image is
`D:\Android\Sdk\system-images\android-30\google_apis\x86_64\system.img`
(sha256 `a38738806b82a340dbe5320c5d6361e95b48cd66ef4cb363725cadee21bb7a0f`).
It is a GPT disk image holding a dynamic-partition `super` partition; the
tools split GPT → liblp → four ext4 images and read the APKs out of them with
`debugfs rdump`. **No emulator was booted and no AVD was created** - the
image was only read.

Only two locale buckets were kept: the default (English) configuration and
every Arabic configuration. Other locales were dropped.

### How the two matching strategies are defined

* **substring** - exactly what the code does: `label.lowercase().contains(entry)`.
  The entry is used **verbatim**; only the label is lower-cased. (Every entry
  in the two lists happens to be lower-case already, so this is currently
  harmless, but it is a latent trap: `String.contains` is case-sensitive and
  `targetLabels` lower-cases the label only.)
* **whole-word** - the entry occurs in the lower-cased label as a whole
  token. The characters either side of the match must not be word characters,
  where word characters are ASCII letters, digits, underscore, **or any
  character in the Arabic blocks** (U+0600-U+06FF, U+0750-U+077F,
  U+08A0-U+08FF, U+FB50-U+FDFF, U+FE70-U+FEFF). This is Java's `\b` with
  `UNICODE_CHARACTER_CLASS`, **not** Java's default ASCII-only `\b` - a
  detail that matters, because with the ASCII-only `\b` the Arabic entries
  would match inside any Arabic word at all.
* **exact** - `label.trim().lowercase() == entry.lower()`, after stripping
  surrounding punctuation and bidi marks.

### How "false positive" is counted

A matched label is counted as a **plausible positive** for an entry when (a)
the entry occurs in it as a whole word **and** (b) the label is a *short*
label (≤ 4 words, ≤ 40 chars), i.e. it looks like a tap-target caption
rather than running prose. Everything else that the strategy matched is a
false positive. The rule is mechanical and reproducible; it is not a claim
about semantics, and it deliberately *over*-credits the matcher (a short
sentence that merely contains the word also counts as plausible). The real
false-positive counts are therefore **lower bounds**.

---

## 2. Per-entry measurement

All counts are over the **82 326 distinct labels**. `inner` is the number of
substring hits that are *not* whole-word hits, i.e. the match sits inside a
longer word - the mechanically unambiguous false positives. `FP(sub)` is the
plausible-positive rule applied to the substring hits. `P(sub)` / `P(word)`
are the plausible-positive ratios. "safe?" is my verdict for that entry
under each strategy.

### 2.1 `sendWords`

| entry | substring | whole-word | exact | inner | FP(sub) | P(sub) | P(word) | example false positives (from the corpus) | safe? sub / word / exact | true positives it would MISS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `send` | 732 | 445 | 2 | 287 | 587 | 0.20 | 0.33 | inner hits: `Sends some cookies and searches from the address bar and search box to your default search engine`, `Touch to Search sends the selected word and the current page as context to Google`; whole-word hits that are not buttons: `Send invitation emails to Google Calendar guests?`, `[DEBUG] Send DB dump` | no / no / no | `resend` (Gmail `sending_timeout_failure_dialog_resend_button`), `sent`, `sending` |
| `submit` | 28 | 21 | 2 | 7 | 19 | 0.32 | 0.43 | `Abuse report not submitted`, `Your feedback has already been submitted`, `Submitting rating…` | marginal / no / no | `submitted`, `Submitting` |
| `post` | 119 | 65 | 1 | 54 | 100 | 0.16 | 0.29 | `Apostrophe`, `Posted`, `Posting to Chat`, and the **HTTP method** `POST` in GMS's Search-API documentation: `Parameters for image URL which uses POST` | no / no / no | `posted`, `Posting` |
| `publish` | 37 | 10 | 1 | 27 | 31 | 0.16 | 0.60 | `Published Site`, `Changing to this draft site setting will allow anyone to view when published.` | no / marginal / no | `published`, `Publishing` |
| `share` | 872 | 510 | 6 | 362 | 679 | 0.22 | 0.38 | `Shared Clipboard`, `shared drive`, `Text shared from %1$s`, `Enable the Shared Clipboard feature…` | no / no / no | `shared`, `Share as photo` is caught, `Share via` is caught |
| `send message` | 24 | 5 | 3 | 19 | 22 | 0.08 | 0.40 | `Resend messages if undelivered`, `You can only send messages to your fixed dialing numbers` | no / no / no | almost everything: the phrase is redundant with `send` (24 hits vs 732) and adds nothing but risk |
| `place order` | 2 | 2 | 1 | 0 | 0 | 1.00 | 1.00 | none | yes / yes / yes | `Buy now`, `order now` |
| `continue` | 276 | 259 | 4 | 17 | 223 | 0.19 | 0.21 | `Continued Conversation`, `you tried to unsubscribe from this sender` | no / no / no | `Continued`, `continuing` |
| `done` | 92 | 75 | 7 | 17 | 52 | 0.44 | 0.53 | **all 17 inner hits are `undone`**: `This action cannot be undone`, `I understand that this action cannot be undone` | marginal / marginal / no | `finished`, `complete` |
| `ok` | 589 | 94 | 5 | 495 | 557 | **0.05** | 0.34 | `Looks good`, `Cook`, `bookings`, `cookies`, `Blocked`, `Room booking screen` - **495 of 589 hits are inside a longer word** | **no** / no / no | `Okay`, `Got it` |
| `yes` | 92 | 40 | 5 | 52 | 60 | 0.35 | 0.80 | `Yesterday`, `Big eyes`, `Small eyes` (52 inner hits) | marginal / yes / no | `yeah` |
| `agree` | 73 | 68 | 2 | 5 | 63 | 0.14 | 0.15 | `Disagree` (5 inner hits - the *opposite* meaning!) | no / no / no | `Accept`, `Accept & continue`, `accepted` |
| `confirm` | 188 | 135 | 3 | 53 | 128 | 0.32 | 0.44 | `Confirmation number: %s`, `View Confirmation`, `Confirming card…`, `Your card is confirmed` | marginal / marginal / no | `Confirmed`, `Confirming…` |
| `إرسال` | 658 | 413 | 2 | 245 | 526 | 0.20 | 0.32 | `عدم الإرسال` (*do not send*), `إيقاف الإرسال` (*stop sending*), `محو الإرسال` (*delete send*), `جارٍ الإرسال` (*sending…*), `زر الإرسال` (*the Send **button***) | no / no / no | `أرسل`, `إرسالها`, `إرسال رسالة` |
| `أرسل` | 9 | 5 | 0 | 4 | 7 | 0.22 | 0.40 | `أرسلنا لك تأكيدًا على طلبك…` (*we sent you…*), `أرسلَت` (past tense inside a sentence) | no / no / **never** | `إرسال` |
| `إرسل` | **0** | 0 | 0 | 0 | 0 | n/a | n/a | - | **dead entry** | every Arabic send caption |
| `مشاركة` | 411 | 254 | 3 | 157 | 322 | 0.22 | 0.35 | `المشاركة` (*the sharing*), `مشاركة الملفات` (*file sharing*) | no / no / no | `مشاركه` (heh spelling) |
| `تأكيد` | 116 | 68 | 2 | 48 | 82 | 0.29 | 0.50 | `رقم التأكيد: %s` (*confirmation number*), `عرض التأكيد` (*view confirmation*), `التأكيد` | marginal / marginal / no | `تأكيدًا` (with tanween) |
| `موافق` | 82 | **6** | 2 | 76 | 78 | **0.05** | 0.67 | `موافقتك` (*your approval*), `تمت الموافقة` (*approval granted*), `نشاط الموافقة` (*approval activity*) | no / **no** / no | `موافقة` (56 labels), `الموافقة` (34), `أوافق` (4) - **whole-word matching loses all of them** |
| `نعم` | 25 | 10 | 2 | 15 | 20 | 0.20 | 0.50 | `نعم، موافق` (that's a *whole-word* hit but not a button), `نعم، احتفظ بنسخة` | no / marginal / no | `نعم،` (12 labels, comma-prefixed) |
| `متابعة` | 171 | 38 | 2 | 133 | 154 | 0.10 | 0.45 | `المتابعة` (*the follow-up*), `المتابعة باسم %1$s`, `القبول والمتابعة` | no / no / no | `المتابعة` (60 labels) |
| `تم` | **4 645** | **1 851** | 3 | **2 794** | **3 984** | 0.14 | 0.36 | the whole-word hits are the Arabic passive particle, not a button: `تم تعيين مدى التوفر إلى: %s` (*availability was set to…*), `تم استبدال الإشعار بـ: %s` | **no** | **no** / no | `تمّ` (302 labels, shadda) |
| `إتمام` | 25 | 21 | 0 | 4 | 20 | 0.20 | 0.24 | `تحتاج إلى الاتصال بالإنترنت لإتمام الدفع.` (*you need a connection to complete the payment*) | no / no / **never** | `إتمامًا` |

### 2.2 `paymentWords`

| entry | substring | whole-word | exact | inner | FP(sub) | P(sub) | P(word) | example false positives (from the corpus) | safe? sub / word / exact | true positives it would MISS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `pay` | 391 | 202 | 1 | 189 | 359 | 0.08 | 0.16 | `China UnionPay`, `Payment methods`, `Pay as you go alerts` | no / no / no | `Paid`, `Paying` |
| `payment` | 168 | 119 | 1 | 49 | 116 | 0.31 | 0.44 | `Payments Summary`, `Billing & payments`, `Advertiser payments affect ad ranking` | marginal / marginal / no | `payments` (plural) is caught by substring only |
| `buy` | 58 | 56 | 1 | 2 | 21 | 0.64 | 0.66 | `Google Partners have a close business relationship with Google and may have paid` | marginal / yes / no | `bought`, `Buy now` is caught |
| `purchase` | 131 | 41 | 0 | 90 | 122 | 0.07 | 0.22 | `Your purchases`, `Purchases`, `Purchased`, `Eligible if purchased.` | no / no / **never** | `purchased`, `purchasing`, and the button `Buy` |
| `checkout` | 33 | 32 | 2 | 1 | 23 | 0.30 | 0.31 | `http://support.google.com/assistant?p=fast_checkout` (a URL) | marginal / marginal / no | `check out` (2 labels, Maps `HOTEL_CHECK_OUT`) - **a different spelling that the list lacks** |
| `subscribe` | 35 | 13 | 1 | 22 | 31 | 0.11 | 0.31 | **`unsubscribe`**: `Report spam & unsubscribe`, `Why is this message in Spam? You tried to unsubscribe from this sender…`, `Unsubscribe tips` | no / no / no | `subscribed`, `subscription`, `subscriptions` |
| `order now` | **0** | 0 | 0 | 0 | 0 | n/a | n/a | - | **dead entry** | the real caption is **`Buy now`** (2 labels) and `Place order` (1) |
| `confirm payment` | 4 | 0 | 0 | 4 | 4 | **0.00** | n/a | all four are prose: `Use face unlock to unlock your device, sign in to apps, and confirm payments.` | no / **never** / never | `تأكيد الدفع`, `إتمام الدفع` |
| `دفع` | 99 | **9** | 1 | 90 | 95 | **0.04** | 0.44 | `طرق الدفع` (*payment methods*), `حفظ طرق الدفع`, `الوصول إلى طرق الدفع` | no / **no** / no | `الدفع` (76 labels), `إتمام الدفع`, `طلب إجراء دفع` - **whole-word matching loses every one of them** |
| `ادفع` | **0** | 0 | 0 | 0 | 0 | n/a | n/a | - | **dead entry** | the whole imperative family |
| `shop` | 81 | 30 | 0 | 51 | 73 | 0.10 | 0.27 | `الشراء` (44) and `شراء` inside `الشراء` | no / no / never | - |
| `اشتر` | 78 | **0** | 0 | 78 | 78 | **0.00** | n/a | `الاشتراك في لعبة من ألعاب اللوحات` (*subscribing to a board game*), `إلغاء الاشتراك` (*cancel subscription*) - it is matching the **subscription** root | no / **never** / never | `الشراء`, `اشترِ`, `اشتري` |
| `اشتري` | 1 | 0 | 0 | 1 | 1 | 0.00 | n/a | `الكونكانية الماهاراشترية` (a *subscription* word) | no / never / never | the whole `اشتر` family |
| `الشراء` | 44 | 40 | 0 | 4 | 34 | 0.23 | 0.25 | `لإكمال عملية الشراء، أضف حساب Google` (*to complete the purchase…*) | no / marginal / never | - |

### 2.3 Two corrections to the ticket's premises

**(a) `"الشراء"` is not a malformed token.** The ticket says it is *"a Latin
`s` inside an Arabic word"* that *"can never match"*. The bytes in
`CapabilityResolver.kt` say otherwise. The 14th entry is
`d9 8a 22 2c 20 22 d8 a7 d9 84 d8 b4 d8 b1 d8 a7 d9 81` = U+0627 U+0644
U+0634 U+0631 U+0627 U+0626 = **ا ل ش ر ا ء**, i.e. *al-šarāʾ*, "the
purchasing" - ordinary Arabic, with a **sheen** U+0634, not a Latin `s`.
It matches **44** corpus labels (40 of them as a whole word), including
`الشراء عبر Google` (*buy with Google*), `تمّ الشراء` (*the purchase was
completed*) and `انخفض سعر الشراء للتو` (*the price of the purchase just
dropped*). Its real defect is different and opposite to the one alleged: it
is the **definite-article** form of the noun `شراء`, so it only fires on
labels that happen to carry the article, and it misses the bare `شراء`
(81 labels) and the imperative `اشتري`. No source change was made, as
instructed; the correction is recorded here.

**(b) The ADR points at the wrong place.** ADR-0003 says the open question is
tracked in `docs/research/reference-analysis.md` §4. §4 of that file has four
items and none of them is about the word lists (item 4 is *Relay operating
cost*). The word-list problem was only ever recorded in the ADR itself.

---

## 3. Which words really appear on real buttons

The corpus contains 31 button-shaped labels (the label, stripped of
punctuation, *is* the action). Counts are of corpus rows.

### English

| caption | rows | caught by `sendWords`/`paymentWords`? | source |
| --- | ---: | --- | --- |
| `Send` | 67 | yes (`send`) | many |
| `Send message` | 7 | yes | Gmail `send_button_content_description` |
| `Send now` | 1 | yes (`send`) | Gmail `confirm_send_to_emergency_number` |
| **`Resend`** | 1 | **only by substring** - whole-word matching loses it | Gmail `sending_timeout_failure_dialog_resend_button` |
| **`Reply`** | 34 | **no - not in the list** | Drive `access_request_reply` |
| **`Forward`** | 10 | **no - not in the list** | Calendar `event_forward` |
| `Share` | 120 | yes (`share`) | Camera2, GMS, Calendar |
| `Share via` | 11 | yes | Chrome `share_link_chooser_title` |
| `Submit` | 32 | yes | Calendar `hats_lib_submit` |
| `Post` | 9 | yes | Maps `OFFERING_ADD_POST_BUTTON` |
| `Publish` | 5 | yes | Maps `PUBLISH_ACTION_BUTTON_ON_LIST_PAGE_TEXT` |
| `Place order` | 1 | yes | Photos `photos_printingskus_retailprints_ui_checkout_button_text` |
| `Pay` | 2 | yes | Chrome `payments_pay_button` |
| `Payment` | 1 | yes | Chrome |
| **`Payments`** | 1 | **only by substring** | GMS `as_clp_payments_info_title` |
| `Buy` | 1 | yes | GMS `purchase_dialog_buy` |
| `Buy now` | 2 | yes (`buy`) | GMS `wallet_buy_now` |
| `Checkout` | 4 | yes | Photos, GMS `rbm_payments_checkout` |
| **`Check out`** | 2 | **no - the list has `checkout`, not `check out`** | Maps `HOTEL_CHECK_OUT` |
| `Subscribe` | 3 | yes | Photos |

### Arabic

| caption | rows | caught? | source |
| --- | ---: | --- | --- |
| `إرسال` | 75 | yes | platform `ime_action_send`, Calendar `accessibility_send_proposal` |
| `إرسال رسالة` | 7 | yes | Chrome `contextmenu_send_message` |
| `تم` | 169 | yes - but see §2.1 | platform `action_mode_done` |
| `مشاركة` | 93 | yes | Camera2 `share` |
| `متابعة` | 94 | yes | platform `autofill_continue_yes` |
| `تأكيد` | 25 | yes | platform `save_password_label` |
| `موافق` | 14 | yes | platform `confirm_battery_saver` |
| `نعم` | 47 | yes | platform `gpsVerifYes` |
| `اشتراك` | 4 | **only by substring** - and only by accident, via the `اشتر` stem | Photos `photos_cloudstorage_ui_buystoragebutton_subscribe_default` |
| `دفع` | 1 | yes | Velvet `pay` |

**The Arabic send button is `إرسال`, not `أرسل`.** `إرسال` is the noun
("the sending") and is what Android's own IME ships as the send action
(`ime_action_send`); 75 corpus rows are the bare caption. `أرسل` is the
imperfect verb ("he sent" / imperative "send!") and appears in only **9**
corpus labels, all of them inside prose (`أرسلنا لك تأكيدًا على طلبك…`,
`هذا المستخدم أرسل صورة`); **not one** is a button caption. `إرسل`, the
third spelling in the list, appears **nowhere at all**.

### Script forms actually used

Counted over the 30 048 distinct labels that contain Arabic script:

| form | labels | note |
| --- | ---: | --- |
| bare alef `ا` U+0627 | 27 813 | dominant |
| yeh `ي` U+064A | 21 649 | |
| teh-marbuta `ة` U+0629 | 16 055 | |
| alef-hamza-below `إ` U+0625 | 10 079 | |
| heh `ه` U+0647 | 9 082 | |
| alef-hamza-above `أ` U+0623 | 7 036 | |
| alef-maksura `ى` U+0649 | 6 603 | |
| yeh-with-hamza `ئ` U+0626 | 3 002 | |
| bare hamza `ء` U+0621 | 3 144 | |
| shadda `ّ` U+0651 | 4 168 | see `تمّ` (302 labels) |
| damma `ُ` U+064F | 1 487 | |
| fatha `َ` U+064E | 831 | |
| kasra `ِ` U+0650 | 643 | |
| alef-madda `آ` U+0622 | 873 | |
| waw-with-hamza `ؤ` U+ؤ | 777 | |
| tatweel `ـ` U+0640 | 227 | |
| sukun `ْ` U+0652 | 54 | |
| farsi yeh `ی` U+06CC | 63 | rare; a Persian-keyboard variant |
| **alef-wasla `ٱ` U+0671** | **0** | never used |
| Arabic-Indic digit `٠` U+0660 | 14 | vs **18 661** labels containing ASCII digits |
| extended Arabic-Indic `۰` U+06F0 | 7 | |

Two consequences:

* **A hamza change is fatal to a substring match.** `إرسال` (10 079 Arabic
  labels contain `إ`) and `أرسل` are different byte sequences. A matcher that
  only strips `أ/إ/آ` to a single alef would fuse them; one that does not
  will miss one of them outright.
* **Tashkeel breaks a literal match.** `تم` (4 645 labels) and `تمّ` (302
  labels) are the same word; a matcher that does not strip U+064B-U+0652
  loses 302 real "Done" captions. `اشترِ` (2 labels) is the same story for
  the buy stem.
* **Digits are overwhelmingly ASCII** (18 661 labels contain ASCII digits vs
  21 that contain Arabic-Indic digits), so digit normalisation is a
  nice-to-have, not a requirement.

---

## 4. What the Arabic list misses

1. **The definite article `ال`.** Arabic is agglutinative and the commonest
   way to nominalise a root is to prefix `ال`. `دفع` appears in 99 labels but
   only 9 of them have it as a whole word; the other 90 are `الدفع`
   ("the payment", 76 labels), `طرق الدفع` ("payment methods"), `إتمام الدفع`
   ("complete the payment"). **Whole-word matching would lose every one of
   them**, and 82 of the 90 are perfectly good "this spends money" signals.
   The same applies to `موافق` (6 whole-word hits vs 56 for `موافقة` and 34
   for `الموافقة`), to `متابعة` (`المتابعة`, 60 labels) and to `اشتر`
   (**0** whole-word hits - it is always a prefix of `اشتراك`, i.e.
   *subscription*).
   *So for Arabic, whole-word matching is not a fix - it is a bug.* The right
   shape is a **stem/prefix match that tolerates a leading `ال` and trailing
   suffixes**, which is what a real Arabic stemmer does.
2. **The imperfect/imperative verbs.** `أرسل` (imperfect "send") is in the
   list but fires 9 times and never on a button; the noun `إرسال` is what
   ships. `ادفع` (imperative "pay!") fires **0** times; the corpus has
   `دفع` (1), `الدفع` (76) and `طلب إجراء دفع` ("request a payment").
   `اشتري` (imperative "buy!") fires **once**, and that once is a
   *subscription* word. The verb forms in the list are the wrong ones; the
   noun forms are the right ones - and the noun forms are already there for
   `send` (`إرسال`) but missing for `pay` (`الدفع` is only reached by
   accident) and `buy` (`الشراء` is there, `شراء` is only reached by
   accident).
3. **Verb morphology that changes the letter.** The corpus contains
   `مشاركه` (with `ه`, the Egyptian spelling): **0** labels - so `مشاركة`
   with teh-marbuta is the right form, but the `ه` variant must be tolerated
   in general.
4. **Sentences, not captions.** 25 % of the Arabic corpus is wrapped in bidi
   control characters (`‏‮Share‬‏`, U+200F / U+202E / U+202C), and 4 284
   Arabic labels contain them. A matcher that trims whitespace only will
   still match (the control characters are not part of the entry), but a
   matcher that uses `\b` must treat them as boundaries, not as word
   characters. Java's default ASCII `\b` happens to do that, but the
   Unicode-aware `\b` does not - another reason the boundary rule has to be
   written out by hand.
5. **Arabic sentences that contain the word but are not actions**, e.g.
   `عدم الإرسال` ("do not send"), `إيقاف الإرسال` ("stop sending"),
   `محو الإرسال` ("delete the sent item"), `جارٍ الإرسال` ("sending…"),
   `تمّ الموافقة` ("approval granted"), `إتمام الدفع` ("complete the
   payment"). These are the *opposite* of the intended action and are the
   single biggest source of false positives in the Arabic list.

---

## 5. Labels that are not words at all

| kind | count | examples |
| --- | ---: | --- |
| **no letters at all** (glyph, punctuation, format string) | 2 036 | `,` `•` `–` `!?#` `!?;,:"()'-/@_` `" — "` `%1$s, %2$s` `\x08` (Gmail `trigger_delete_char`) |
| **resource-id / localisation key shipped as a value** | 601 | `holidays_android`, `cross_profile`, `smart_mail`, `about_key`, `allow_get_location`, `always_true`, `app_restrictions_exchange_authentication_type_value_modern` |
| **icon named instead of the action** (icon-button content descriptions) | 286 | `Dialog Icon`, `Info Icon`, `Down arrow` / `Left arrow` / `Right arrow` / `Insertion arrow` (Gboard key content descriptions), `Sticker set icon`, `leftwards arrow with stroke` / `rightwards arrow with stroke` (`unicode_219A`/`219B` - the **Unicode character name** used as a content description) |
| **a reference to a button rather than the button** | many | `زر الإرسال` (*the Send button*), `send_button_content_description` |
| **mixed script** | 7 885 | `ملف PDF`, `خدمات Google Play`, `Google Fit` - a Latin brand name inside an Arabic label, which is the norm in the Google apps |
| **bidi control characters** | 15 985 (4 284 Arabic) | `‏‮Share‬‏` |
| **prefix/punctuation variants of a caption** | many | `تم.` `نعم،` `الشراء` `Send now` `Resend` |
| **empty / null content description** | **not measurable** | see §7 |

Two things follow.

* The **icon case that ADR-0003 calls "the serious one" is real and it is
  nameable**: 286 corpus labels are content descriptions that *name an icon*
  (`Info Icon`, `Down arrow`, `leftwards arrow with stroke`) instead of naming
  the action. Such a node is unclassifiable from its label, and no word list
  can fix it.
* The **"localisation key shipped as a value"** case is real too: 601 corpus
  labels are snake_case identifiers. Six of them contain `ok` and would be
  escalated to `MESSAGE_SEND` by the current matcher:
  `auth_token` (`pref_key_auth_token`), `handwriting_stroke_width_scale`,
  `mobile_bookmarks` (`help_context_bookmarks`), `voice_auth_token`,
  `voice_auth_token_account`, `voice_auth_token_expire_time`. A key is not a
  *label*, so a matcher that treats it as one is matching noise.

---

## 6. Recommendation

**Replace the two lists; do not merely narrow or supplement them.** The
numbers say the lists are not a detector with a bad threshold, they are a
detector whose signal is mostly noise: of the 20 ASCII entries the median
plausible-positive ratio is **0.20**, the best is `buy` at **0.64** (and
`place order` at 1.00, but it fires on 2 labels); of the 14 Arabic entries
the best is `تأكيد` at **0.29**, and `اشتر` and `اشتري` score **0.00** while
`دفع` scores **0.04**.

Concretely, in priority order:

1. **Stop matching on substrings. Match on a normalised token set.**
   Normalise the label (lower-case, strip bidi control characters, strip
   tashkeel, unify `أ/إ/آ/ٱ` → `ا`, unify `ى/ی` → `ي`, unify `ة/ه` → `ه`,
   strip a leading `ال` from Arabic tokens, drop trailing `ً/ِ/ُ`), split into
   tokens, and match tokens against a **stem** set. That single change kills
   the 495 `ok` hits inside `Look`/`Cook`/`bookings`, the 189 `pay` hits
   inside `UnionPay`/`Payment`, the 90 `دفع` hits inside `الدفع`-style
   prefixes *without* losing `الدفع`, and the 22 `subscribe` hits inside
   `unsubscribe` - while *keeping* the `تم`/`تمّ` and `اشتر`/`اشترِ` pairs
   together.
2. **Shrink the concept set to the captions that actually ship.** From §3:
   *send* → `send`, `send message`, `send now`, `resend`, `submit`, `post`,
   `publish`, `share`, `reply`, `forward`; *pay* → `pay`, `payment(s)`,
   `buy`, `buy now`, `purchase`, `checkout`, `check out`, `subscribe`,
   `subscription`, `order now`, `place order`, `confirm payment`. In Arabic:
   `إرسال`, `إرسالها`, `أرسل`, `مشاركة`, `تم`, `تأكيد`, `موافق/موافقة`,
   `نعم`, `متابعة`; `دفع`, `الدفع`, `ادفع`, `اشتر`, `اشتري`, `شراء`,
   `الشراء`, `اشتراك`, `إتمام الدفع`. Drop the four dead entries
   (`إرسل`, `order now`, `ادفع`, `اشتري` as standalone entries) or keep them
   only as stems that the normaliser can actually reach.
3. **Do not use a bare `ok`/`yes`/`done`/`تم` as a trigger.** `تم` fires on
   1 851 whole-word labels and 495 of them are the passive particle
   "has been …". If a confirm-style button must escalate, require *both* a
   matching word **and** corroborating context (see point 5).
4. **Prefer the other signals the accessibility node already carries.**
   `ActionContext` already has `targetClass`. A node whose class is
   `android.widget.Button` and whose text is exactly `إرسال` is a different
   proposition from a paragraph that happens to contain the word. The
   *corpus* says a button caption is short: 49 121 of 82 326 labels are
   ≤ 4 words, and the escalation decision should probably be restricted to
   short captions. That alone would remove the `تم تعيين التقويم إلى: %s`
   class of false positives.
5. **Add a context signal, not just a word signal.** A `MESSAGE_SEND`
   escalation is much more trustworthy when the press happened inside a
   composer, or when the node's text is one of the handful of *exact*
   captions. The corpus supports an **exact-caption** rule for the
   escalation trigger, because the exact-caption set is small and
   well-defined (§3). The `exact` column of the tables above is the size of
   that set today: 2-7 labels per entry. That is a list a human can review,
   which is the point.

### Is a per-package allow-list of known send/payment surfaces worth it?

**As a *primary* mechanism: no.** ADR-0003 already rejected per-package
tiers for exactly this reason (jurisdiction-specific, perpetually out of
date), and the corpus shows why: the send/payment surface of a real app is a
*button inside a screen*, not a package. `Chrome` has both a `payments_pay_button`
and a `contextmenu_send_message`; `Maps` has `HOTEL_CHECK_OUT` and
`OFFERING_ADD_POST_BUTTON`; the same package is both safe and dangerous
depending on the screen.

**As a *supplementary* signal: yes, but a different one.** The corpus
supports a **per-package allow-list of known *scenes*** - "the Play Billing
dialog in com.android.vending", "the Gmail compose screen" - *if* it is
maintained as data, versioned, and only ever used to **add** suspicion, never
to clear it. Two concrete facts from the corpus justify it:

* The *package* is a weak signal: **27 of the 108 APKs** that declare string
  resources contribute nothing to either list, and the same package
  contributes both true and false positives.
* The *view id* is a strong signal and is already in the accessibility tree:
  the corpus shows the real buttons are named `send_button_content_description`,
  `photos_printingskus_retailprints_ui_checkout_button_text`,
  `wallet_buy_now`, `rbm_payments_checkout`,
  `sending_timeout_failure_dialog_resend_button`,
  `photos_cloudstorage_ui_buystoragebutton_subscribe_default`. A
  **view-id pattern list** (`*send*button*`, `*checkout*`, `*buy*now*`) is a
  far better allow-list than a package list, because it is screen-agnostic
  and locale-agnostic, and it is exactly the data `AccessibilityNodeInfo`
  exposes. It should be an **additional** trigger, not a replacement for the
  caption match - it catches the icon case (§5) that no caption match can.

### Ordering of the work

1. Normalise + tokenise (point 1). This is pure Kotlin in the protocol
   module, testable against `docs/research/label-corpus.txt`.
2. Replace the lists with the curated set (point 2) and add a regression
   test that runs the matcher over the corpus and asserts the false-positive
   budget. The corpus file makes such a test possible, which is the main
   reason to keep it in the repo.
3. Add the exact-caption / short-caption gates (points 4-5) and the
   view-id pattern trigger.
4. Only then consider package-level data, and only as an *additional*
   trigger.

---

## 7. What this corpus could NOT answer

* **Not measured: what a real accessibility tree contains.** The corpus is
  *resource tables*, so it tells us what strings exist, not what is actually
  on screen. It cannot say how often a given button is actually tapped, or
  how often a long paragraph is a content description rather than a caption.
* **Not measured: strings hard-coded in code or built at runtime.** Only
  declared string resources are in the corpus. An app that does
  `setText("Send")` in Java is invisible here, and so is a string assembled
  from a format at runtime. The corpus therefore **under-counts** the number
  of distinct "Send" captions in the wild and **over-counts** the share of
  labels that are short captions (resource tables are full of prose).
* **Not measured: empty or null content descriptions.** By construction a
  null `contentDescription` leaves no string resource behind, so the
  286 icon-named descriptions in §5 are a *lower bound* on the number of
  icon-only buttons. The rate of unlabeled buttons cannot be measured from
  a resource corpus at all - it needs a screen scrape or an instrumented
  device.
* **Not measured: per-element class and view id.** The corpus has the
  *resource* names, not the view hierarchy, so the "view-id pattern" idea in
  §6 is supported by the *naming convention* of the shipped resources, not
  by a measured hit rate.
* **Not measured: the frequency of a false positive mattering.** Every label
  in the corpus is equally weighted here. In the field, `ok` inside
  `look up` in a search box is far more common than `ok` inside a rare
  prose string, and that difference changes the practical severity.
* **Not measured: the Arabic gap in third-party apps.** The Arabic strings
  here are Google's. Egyptian/Gulf apps, apps that ship their own
  translation, and apps that use a right-to-left SDK (or a third-party SDK
  with machine-translated strings) are all outside the corpus. The task
  suggested the web as a third source; it was not needed for the questions
  asked, but it would be the first place to look for "how a *non-Google*
  Arabic app labels its send button".
* **Not measured: what an Arabic speaker would call a "false positive".**
  The plausible-positive rule used here is mechanical and English-centric
  ("≤ 4 words and ≤ 40 characters"). It is a proxy, not a judgement.
* **No emulator was used.** The AGENTS.md rule was respected: the system
  image was read as a file, never booted, and no AVD was created.
