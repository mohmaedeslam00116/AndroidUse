# ADR-0007: Arabic is a first-class language, not a translation layer

- Status: Accepted
- Date: 2026-10-20

## Context

The user requirement is explicit: "the user can give commands in Arabic or
English". None of the reference projects supports this in any real sense.

- **ClosePaw** — English-only UI, English-only system prompt. It does have a
  `SpeechRecognizer` path for dictation.
- **CellClaw** — no `values-ar` directory at all, all UI strings hardcoded
  inline in Compose, and `strings.xml` holds five strings, none of them used
  for UI text. `android:supportsRtl="true"` is declared and nothing else is
  done about it. No Arabic prompt, no Arabic TTS/STT beyond
  `Locale.getDefault()`.
- **android-agent** — no Arabic strings, no `values-ar`, no `SpeechRecognizer`,
  no `TextToSpeech` at all. Its `Diagnostics` even hardcodes `Locale.UK` for
  timestamps.

A bilingual product built by translating an English one at the end is a
translation of the *UI*, but it does nothing for the hard parts: the Agent's
system prompt, the model's reasoning about an Arabic screen, the
acknowledgement wording, and the approval request.

## Decision

Arabic is a **product locale**, not a localisation pass. Four things are true
by construction, not by translation:

1. **The Agent thinks in the user's language.** The Run carries the language
   the user used. The Relay's system prompt is assembled in that language, and
   the Agent is instructed to reason in it. The Relay does not translate the
   Goal into English and back.
2. **The UI is a real RTL UI.** `values-ar/strings.xml` exists, every string
   is extracted, and layout uses `start`/`end` rather than `left`/`right`.
   Compose's `LocalLayoutDirection` is driven by the locale, not forced.
3. **Arabic screens are first-class perception.** An Android app rendered in
   Arabic produces an accessibility tree whose text is Arabic. The Tree
   channel therefore carries Arabic directly, and the Frame channel shows
   Arabic glyphs. We do not OCR-translate; the model reads the same text the
   user sees.
4. **Voice input and output are locale-aware.** `SpeechRecognizer` and
   `TextToSpeech` are driven by the Run's language, not by
   `Locale.getDefault()`, so an Arabic-speaking user on an English phone can
   still dictate in Arabic.

The Agent's *reasoning* stays in one language per Run. Mixed-language Runs
(the user types Arabic, the app on screen is English) are handled by the
prompt, not by switching languages mid-Run.

## Consequences

**Good**

- The Agent can act on Arabic-labelled elements, because the Tree channel
  gives it the Arabic text, not a transliteration.
- The user reads approval requests, the transcript, and the final answer in
  their own language.
- Arabic numerals, RTL text mixing, and the way Arabic apps actually lay out
  are exercised from the first Run rather than at the end.

**Bad, and accepted**

- Every string in the app must be extracted from the start, and both locales
  must be kept in step. This is slower to write and it is the only way to
  avoid the CellClaw outcome of hardcoded English with a five-string
  `strings.xml`.
- The system prompt has to be authored and maintained in both languages, and
  a mistranslated prompt degrades the Agent's behaviour in that language.
  Prompt text lives in the Relay, versioned with the rest of it.
- RTL layout bugs are a category of work that English-first teams skip. We
  take them on deliberately.

**Neutral**

- English remains the default when the user's language cannot be determined.

## Alternatives considered

**Ship English first, add Arabic later.** Rejected: it is how the references
ended up with no Arabic at all, and it defers the hardest part (the prompt and
the Tree channel) to the end, when it is most expensive to change.

**Translate the Goal to English for the Agent, translate the answer back.**
Rejected: it loses the Arabic text on screen, which is exactly what the Agent
needs to ground on.

**On-device translation.** Rejected: adds a dependency and a failure mode for
no benefit — the model handles both languages natively.

## Related

- [ADR-0002](0002-mediaprojection-primary-perception.md) — the perception
  channels that carry Arabic
- [ADR-0004](0004-native-computer-use-action-set.md) — the action schema,
  which is language-neutral
