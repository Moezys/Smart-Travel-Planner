import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso))
}

export function totalCost(usage: {
  cheap_in: number; cheap_out: number; strong_in: number; strong_out: number
}) {
  // Gemma-4-31b-it approximate pricing ($/1M tokens)
  const CHEAP_IN = 0.14, CHEAP_OUT = 0.28
  const STRONG_IN = 0.14, STRONG_OUT = 0.28
  const cost =
    (usage.cheap_in * CHEAP_IN + usage.cheap_out * CHEAP_OUT +
     usage.strong_in * STRONG_IN + usage.strong_out * STRONG_OUT) / 1_000_000
  return cost.toFixed(5)
}
