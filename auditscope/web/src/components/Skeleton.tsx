export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-lg bg-bg-700/60 ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-line bg-bg-800/70 p-5">
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="mt-3 h-4 w-2/3" />
      <Skeleton className="mt-2 h-4 w-1/2" />
    </div>
  )
}
