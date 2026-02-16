# Accessibility Adaptation Reference

## UDL Quick Reference (CAST Framework)

| Principle | Key Strategies |
|-----------|---------------|
| Engagement | Choice, relevance, self-regulation, mastery feedback |
| Representation | Multi-modal, vocabulary support, background knowledge |
| Action & Expression | Multiple response formats, assistive tech, planning tools |

## Adaptation Matrix by Need

### TEA (Autism Spectrum)
| Area | Adaptation | Example |
|------|-----------|---------|
| Predictability | Visual schedule, step-by-step | Numbered checklist with time estimates |
| Sensory | Low-stimulus layout, calm colors | Remove animations, reduce visual clutter |
| Communication | Explicit instructions, no idioms | "Write 3 sentences" not "express your thoughts" |
| Transitions | Advance warning, scripts | "In 2 minutes we will change to..." |
| Breaks | Scheduled regulation pauses | Timer every 8-10 min for self-check |

### TDAH (ADHD)
| Area | Adaptation | Example |
|------|-----------|---------|
| Attention | Short chunks (5-10 min) | Break lesson into 3 micro-activities |
| Organization | Checklists, visual timers | "Done" checkpoints after each section |
| Movement | Active learning, breaks | Stand-up activities between seated work |
| Focus | Reduce distractions, clear goals | Single task visible at a time |
| Feedback | Immediate, specific | Check after each step, not end only |

### Learning Difficulties (Dyslexia, etc.)
| Area | Adaptation | Example |
|------|-----------|---------|
| Reading | Larger font, line spacing, sans-serif | OpenDyslexic or similar font |
| Vocabulary | Glossary, word bank | Key terms defined before use |
| Instructions | Model before practice | Worked example, then guided practice |
| Response | Alternative outputs | Oral, drawing, MCQ alongside written |
| Scaffolding | Examples first, then abstraction | Concrete → pictorial → abstract |

### Hearing Impairment
| Area | Adaptation | Example |
|------|-----------|---------|
| Audio content | Captions, transcripts | All videos captioned, all audio transcribed |
| Instructions | Written + visual | Never audio-only instructions |
| Discussion | Speaker identification | Name labels in transcripts |
| Assessment | Visual alternatives | Written/visual instead of oral |
| Sign language | Libras/ASL glosses | Translated content when available |

### Visual Impairment
| Area | Adaptation | Example |
|------|-----------|---------|
| Images | Alt text, audio description | Detailed descriptions of all visuals |
| Layout | Semantic HTML, headings | Screen reader navigable |
| Text | Large print, high contrast | 16pt+, 4.5:1 contrast ratio |
| Color | Not sole information carrier | Add patterns, labels alongside color |
| Navigation | Keyboard accessible | Full keyboard control, skip links |

## Export Format Recommendations

| Format | For | Accessibility |
|--------|-----|---------------|
| `low_distraction_html` | TEA, TDAH | Minimal UI, calm colors, no animations |
| `large_print_html` | Visual, learning | 18pt+, extra spacing, high contrast |
| `screen_reader_html` | Visual | Semantic HTML, aria-labels, headings |
| `visual_schedule_html` | TEA | Step-by-step with images, timers |
| `student_plain_text` | All | Simplified language, short sentences |
| `audio_script` | Visual, learning | TTS-ready narration |
| `caption_transcript` | Hearing | Full text of all audio/video |
