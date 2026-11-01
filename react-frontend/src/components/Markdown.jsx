// Minimal, safe markdown renderer (no dangerouslySetInnerHTML).
// Supports: #-headings, **bold**, `code`, lists, tables, --- and <br/> from Asha replies.

function inline(text, keyBase) {
  const parts = []
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g
  let last = 0
  let m
  let i = 0
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index))
    const tok = m[0]
    const k = `${keyBase}-${i++}`
    if (tok.startsWith('**')) parts.push(<strong key={k}>{tok.slice(2, -2)}</strong>)
    else if (tok.startsWith('`')) parts.push(<code key={k}>{tok.slice(1, -1)}</code>)
    else parts.push(<em key={k}>{tok.slice(1, -1)}</em>)
    last = m.index + tok.length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

export default function Markdown({ text = '' }) {
  const lines = String(text).replace(/<br\s*\/?>/gi, '\n').split(/\r?\n/)
  const out = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]
    const t = line.trim()
    if (!t) { i++; continue }

    if (/^#{1,6}\s/.test(t)) {
      const level = Math.min(3, t.match(/^#+/)[0].length)
      const H = `h${level}`
      out.push(<H key={key++}>{inline(t.replace(/^#+\s*/, ''), key)}</H>)
      i++; continue
    }
    if (/^(-{3,}|\*{3,})$/.test(t)) { out.push(<hr key={key++} />); i++; continue }

    if (t.startsWith('|')) {
      const rows = []
      while (i < lines.length && lines[i].trim().startsWith('|')) { rows.push(lines[i].trim()); i++ }
      const cells = (r) => r.replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
      const body = rows.filter((r) => !/^\|[\s:|-]+\|?$/.test(r))
      const [head, ...rest] = body
      out.push(
        <div className="table-wrap" key={key++} style={{ maxHeight: 360 }}>
          <table>
            <thead><tr>{cells(head).map((c, j) => <th key={j}>{inline(c, `h${j}`)}</th>)}</tr></thead>
            <tbody>{rest.map((r, ri) => <tr key={ri}>{cells(r).map((c, j) => <td key={j}>{inline(c, `${ri}-${j}`)}</td>)}</tr>)}</tbody>
          </table>
        </div>,
      )
      continue
    }

    if (/^([-*•]|\d+\.)\s/.test(t)) {
      const ordered = /^\d+\./.test(t)
      const items = []
      while (i < lines.length && /^([-*•]|\d+\.)\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^([-*•]|\d+\.)\s+/, ''))
        i++
      }
      const L = ordered ? 'ol' : 'ul'
      out.push(<L key={key++}>{items.map((it, j) => <li key={j}>{inline(it, `${key}-${j}`)}</li>)}</L>)
      continue
    }

    out.push(<p key={key++}>{inline(t, key)}</p>)
    i++
  }
  return <div className="md">{out}</div>
}
