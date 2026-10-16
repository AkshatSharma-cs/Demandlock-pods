# Pre-recorded voice clips

Twelve clips total: 4 message keys × 3 recorded languages. Telugu (`te`) uses
text-to-speech fallback until clips are recorded.

| Key | English source sentence | Hindi file | Tamil file | English file |
| --- | --- | --- | --- | --- |
| `welcome` | Welcome to DemandLock Pods. | `/audio/hi/welcome.mp3` | `/audio/ta/welcome.mp3` | `/audio/en/welcome.mp3` |
| `practice_task` | Practice task: repair a screen protector fitting and show your teacher. | `/audio/hi/practice_task.mp3` | `/audio/ta/practice_task.mp3` | `/audio/en/practice_task.mp3` |
| `safeguard_message` | You are under 18, so you can join supervised practice only. No work placement. | `/audio/hi/safeguard_message.mp3` | `/audio/ta/safeguard_message.mp3` | `/audio/en/safeguard_message.mp3` |
| `pod_explanation` | This pod fits you because you like repairing phones. Pay is unknown until the employer confirms. | `/audio/hi/pod_explanation.mp3` | `/audio/ta/pod_explanation.mp3` | `/audio/en/pod_explanation.mp3` |

## Recording requirements

- A native speaker must translate and record the `hi` and `ta` clips; do not
  machine-translate the source sentences.
- Keep every clip under 10 seconds.
- Export as mono MP3 at 64 kbps.
- Filename must be exactly `{lang}/{key}.mp3` under this `audio/` folder.

## Offline / DevOps note

Precache `/audio/**` in the service worker so the demo plays offline after the
first visit. The speak() function treats a clip that cannot be fetched or
played as a cache miss and falls back to `speechSynthesis`.