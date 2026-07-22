import { useEffect, useRef, useState } from 'react'

export function useCountUp(target, duration = 600) {
  const [value, setValue] = useState(target)
  const fromRef = useRef(target)
  const frameRef = useRef(null)

  useEffect(() => {
    const from = fromRef.current
    const to = typeof target === 'number' && !isNaN(target) ? target : 0
    const start = performance.now()

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      setValue(to)
      fromRef.current = to
      return
    }

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(from + (to - from) * eased)
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick)
      } else {
        fromRef.current = to
      }
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
  }, [target, duration])

  return value
}