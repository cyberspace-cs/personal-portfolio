import { marked } from 'marked'
import DOMPurify from 'dompurify'

export function Markdown({ source }: { source: string }) {
  const html = DOMPurify.sanitize(marked.parse(source, { async: false }) as string)
  return <div className="prose-cs" dangerouslySetInnerHTML={{ __html: html }} />
}
