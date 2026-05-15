export function StatusBar({ message }: { message: string }) {
  return (
    <div className="h-7 bg-panel border-t border-rule px-4 flex items-center text-[11px] text-stone">
      <span className="truncate">{message}</span>
    </div>
  )
}
