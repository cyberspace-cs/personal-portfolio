interface Col<T> { key: string; label: string; render?: (row: T) => React.ReactNode; cls?: string }
export function DataTable<T extends Record<string, any>>({ cols, rows }: { cols: Col<T>[]; rows: T[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full text-left text-sm">
        <thead className="bg-bg-700/60 text-slate-400">
          <tr>
            {cols.map(c => (
              <th key={c.key} className={`px-4 py-3 font-medium ${c.cls ?? ''}`}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((r, i) => (
            <tr key={i} className="bg-bg-800/40 transition-colors hover:bg-bg-700/50">
              {cols.map(c => (
                <td key={c.key} className="px-4 py-3 text-slate-200">{c.render ? c.render(r) : r[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
