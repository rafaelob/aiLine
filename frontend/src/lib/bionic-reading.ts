/**
 * Transform text into Bionic Reading format.
 * Bolds the first half of each word to guide eye fixation,
 * helping students with dyslexia and ADHD.
 */
export function toBionicHtml(text: string): string {
  return text.replace(/\b(\w+)\b/g, (word) => {
    const mid = Math.ceil(word.length / 2)
    const bold = word.slice(0, mid)
    const rest = word.slice(mid)
    return `<b>${bold}</b>${rest}`
  })
}
