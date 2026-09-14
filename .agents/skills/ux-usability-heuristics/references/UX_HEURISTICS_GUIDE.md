# UX Heuristics Evaluation Guide

> Freshness: written March 2026. Nielsen's heuristics are stable principles, but verify WCAG version and platform guidelines against current official sources.

## Conducting a Heuristic Evaluation

### Preparation
1. Define the scope: which flows/screens to evaluate.
2. Identify evaluator(s): 3-5 evaluators find ~75% of usability issues.
3. Gather materials: user personas, task scenarios, success criteria.
4. Set up evaluation template (see below).

### Evaluation process
1. Walk through each task scenario independently (each evaluator alone).
2. For each screen/interaction, check against all 10 heuristics.
3. Document findings with: location, heuristic violated, severity, evidence (screenshot), recommendation.
4. Aggregate findings. Deduplicate. Prioritize by severity.
5. Present findings with actionable fixes, not just problem descriptions.

## Severity Rating Scale

| Rating | Label       | Impact                                     | Action           |
|--------|-------------|---------------------------------------------|------------------|
| 0      | Not a problem | Evaluator opinion, not a real usability issue | None           |
| 1      | Cosmetic    | Noticeable but does not impede task completion | Fix if time allows |
| 2      | Minor       | Causes minor confusion or delay              | Low priority fix  |
| 3      | Major       | Significant user difficulty, task may fail    | Important to fix  |
| 4      | Catastrophe | Users cannot complete the task; data loss risk | Must fix before release |

Severity factors: frequency (how often), impact (how severe when it occurs), persistence (one-time or recurring).

## Finding Template

```
FINDING #[number]
Location: [screen/component/URL]
Heuristic: [number and name]
Severity: [0-4]
Description: [what the problem is]
Evidence: [screenshot or observation]
User impact: [what happens to the user]
Recommendation: [specific fix with rationale]
```

## Heuristics Quick-Reference with Modern Examples

### H1: Visibility of System Status
- Good: Skeleton screens during data loading. Real-time character count on text inputs. Upload progress with percentage and time estimate.
- Bad: Spinner with no context ("Loading..."). No feedback after form submission. Async operations with no status indicator.

### H2: Match Between System and Real World
- Good: Shopping "cart" metaphor. Calendar widget for date selection. Error messages in plain language.
- Bad: "Transaction 40X failed: ERR_TIMEOUT". Technical field names in user-facing forms. Icons without labels that require domain knowledge.

### H3: User Control and Freedom
- Good: Undo after email send (Gmail's undo). Draft auto-save every 30 seconds. "Back" button works predictably. Multi-level undo/redo.
- Bad: No way to cancel a multi-step process. Accidental deletion with no recovery. Forced wizard with no skip or back option.

### H4: Consistency and Standards
- Good: Same icon always means the same thing. Consistent button placement across screens. Platform-standard gestures (swipe to delete on iOS).
- Bad: "Save" sometimes at top, sometimes at bottom. Different date formats on different pages. Non-standard icons for common actions.

### H5: Error Prevention
- Good: Inline validation before submission. Confirmation for destructive actions. Date pickers prevent invalid dates. Auto-save prevents data loss.
- Bad: Free text for structured data (dates, phone numbers). Delete button next to Edit with no confirmation. Form accepts then rejects data server-side.

### H6: Recognition Rather Than Recall
- Good: Autocomplete with recent searches. Breadcrumbs showing navigation path. Inline help at complex fields. Dashboard showing recent items.
- Bad: Requiring users to remember codes/IDs. Settings with no search function. Error messages referencing field names not visible on screen.

### H7: Flexibility and Efficiency of Use
- Good: Keyboard shortcuts listed in tooltips. Bulk select and act on multiple items. Saved filters/views. Command palette (Cmd+K).
- Bad: No keyboard navigation. Repetitive tasks without batch operations. No way to customize or pin frequent actions.

### H8: Aesthetic and Minimalist Design
- Good: Progressive disclosure (show more on demand). Clean content hierarchy. Whitespace separating logical groups. One primary CTA per context.
- Bad: Cluttered dashboards with everything visible. Decorative elements competing with content. Multiple equally-weighted CTAs causing decision paralysis.

### H9: Help Users Recover from Errors
- Good: "Your password must include a number and special character" (specific). Inline field errors next to the field. Suggested corrections for search typos.
- Bad: "Invalid input" (vague). Error displayed only at top of long form. Raw HTTP status codes or stack traces.

### H10: Help and Documentation
- Good: Contextual tooltips at decision points. Searchable help center. Onboarding tour for new features. AI-assisted help that understands context.
- Bad: Documentation only as separate PDF. No search in help center. Help content written for developers, not users.

## Evaluation Report Structure

1. **Executive summary:** total findings by severity, top 3 critical issues.
2. **Methodology:** evaluators, scenarios, heuristics used, evaluation date.
3. **Findings by severity:** severity 4 first, then 3, 2, 1.
4. **Findings by flow:** group related issues for implementation efficiency.
5. **Recommendations:** prioritized action items with estimated effort.
6. **Appendix:** all findings with screenshots and detailed evidence.

## Integrating with Development

- File severity 3-4 findings as bugs with "ux" label.
- File severity 1-2 findings as improvement tickets.
- Include acceptance criteria: "User can [task] without [problem]".
- Re-evaluate after fixes are implemented (verify, not just close).
- Track fix rate and mean time to resolve UX issues.

## Key Links
- Nielsen's heuristics (original): https://www.nngroup.com/articles/ten-usability-heuristics/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Material Design 3 guidelines: https://m3.material.io/
- Apple HIG: https://developer.apple.com/design/human-interface-guidelines/
- Inclusive design: https://inclusive.microsoft.design/
