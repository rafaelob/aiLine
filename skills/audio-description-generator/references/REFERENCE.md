# Audio Description & Alt Text Reference

## WCAG 2.2 Image Requirements

| Level | Requirement |
|-------|------------|
| A (1.1.1) | All non-text content has a text alternative |
| A (1.2.1) | Audio-only/video-only: alternative provided |
| A (1.2.3) | Audio description for pre-recorded video |
| AA (1.2.5) | Audio description for all pre-recorded video |
| AAA (1.2.7) | Extended audio description when pauses insufficient |
| AAA (1.2.8) | Full text alternative for pre-recorded media |

## Alt Text Decision Tree

1. Is the image decorative? → `alt=""`
2. Is it a link/button? → Describe the function, not the image
3. Is it a simple image? → Describe content + purpose in alt attribute
4. Is it complex (chart, diagram)? → Brief alt + longdesc/aria-describedby

## Description Templates

### Bar Chart
"Bar chart comparing [topic] across [categories]. The X-axis shows [label] and
the Y-axis shows [label] from [min] to [max]. [Category A] has the highest value
at [N], followed by [Category B] at [N]. The data shows that [key insight]."

### Line Graph
"Line graph showing [topic] over [time period]. The X-axis spans [start] to [end],
Y-axis measures [label] from [min] to [max]. The trend shows [description]:
[specific data points]. Notable: [peak/valley/intersection at specific point]."

### Pie Chart
"Pie chart showing the distribution of [topic]. The largest segment is [Category]
at [N]%, followed by [Category] at [N]%. [Two smallest categories] together
represent [N]% of the total."

### Diagram/Flowchart
"Flowchart with [N] steps showing [process]. Starting with [first element],
the flow proceeds to [second element]. At [decision point], the path splits:
[condition A] leads to [outcome A], while [condition B] leads to [outcome B].
The process concludes at [final element]."

### Scientific Diagram
"Labeled diagram of [subject] showing [N] main components. [Component A] is
located [position] and connects to [Component B] via [connection type].
Key features include [list]. The diagram illustrates [educational concept]."

## Audio Description Timing

- Standard: 150-180 words per minute
- Extended pauses: 2-3 seconds between major sections
- Math/science: slower pace (120-150 wpm) with emphasis on relationships
- Allow processing time after data-heavy descriptions

## Language Best Practices

| Do | Don't |
|----|-------|
| "A bar chart showing..." | "Image of a bar chart..." |
| "Three students work together" | "A picture shows some kids" |
| "The largest segment, at 45%..." | "The biggest piece..." |
| Use specific numbers and labels | Use vague descriptions |
| Describe spatial relationships | Assume visual understanding |
| Include colors when meaningful | Describe every color if irrelevant |
