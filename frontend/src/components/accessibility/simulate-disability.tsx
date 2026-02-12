'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { SIMULATIONS, SIMULATION_CATEGORIES, getSimulationCSS } from '@/lib/accessibility-data'
import { useDyslexiaSimulator } from '@/hooks/use-dyslexia-simulator'
import type { SimulationMode } from '@/types/accessibility'

/**
 * Empathy Bridge -- "Simulate Disability" mode for educators.
 * Applies CSS filters/effects to the page so teachers can experience
 * how students with different conditions perceive the content.
 *
 * Simulations:
 * - Color blindness (protanopia, deuteranopia, tritanopia) via SVG feColorMatrix (Brettel 1997)
 * - Low vision (blur + reduced contrast)
 * - Dyslexia (letter shuffling via useDyslexiaSimulator hook)
 * - Tunnel vision (radial gradient mask overlay)
 * - Motor difficulty (cursor delay)
 */
export function SimulateDisability() {
  const [activeSimulations, setActiveSimulations] = useState<Set<SimulationMode>>(new Set())
  const tunnelOverlayRef = useRef<HTMLDivElement | null>(null)

  const isDyslexiaActive = activeSimulations.has('dyslexia')
  const { startSimulation: startDyslexia, stopSimulation: stopDyslexia } =
    useDyslexiaSimulator(isDyslexiaActive)

  const toggleSimulation = useCallback(
    (mode: SimulationMode) => {
      setActiveSimulations((prev) => {
        const next = new Set(prev)
        if (next.has(mode)) {
          next.delete(mode)
        } else {
          next.add(mode)
        }
        return next
      })
    },
    [],
  )

  const resetAll = useCallback(() => {
    setActiveSimulations(new Set())
  }, [])

  // Apply visual filter simulations to document.documentElement
  useEffect(() => {
    const filters: string[] = []

    for (const mode of activeSimulations) {
      const css = getSimulationCSS(mode)
      if (css) {
        filters.push(css)
      }
    }

    document.documentElement.style.filter = filters.length > 0 ? filters.join(' ') : ''

    return () => {
      document.documentElement.style.filter = ''
    }
  }, [activeSimulations])

  // Tunnel vision overlay
  useEffect(() => {
    if (activeSimulations.has('tunnel_vision')) {
      const overlay = document.createElement('div')
      overlay.id = 'tunnel-vision-overlay'
      overlay.setAttribute('aria-hidden', 'true')
      overlay.style.cssText = [
        'position: fixed',
        'inset: 0',
        'z-index: 9999',
        'pointer-events: none',
        'background: radial-gradient(circle 200px at var(--mouse-x, 50%) var(--mouse-y, 50%), transparent 0%, rgba(0,0,0,0.95) 100%)',
      ].join(';')
      document.body.appendChild(overlay)
      tunnelOverlayRef.current = overlay

      const handleMouseMove = (e: MouseEvent) => {
        overlay.style.setProperty('--mouse-x', `${e.clientX}px`)
        overlay.style.setProperty('--mouse-y', `${e.clientY}px`)
      }
      window.addEventListener('mousemove', handleMouseMove)

      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        overlay.remove()
        tunnelOverlayRef.current = null
      }
    }
  }, [activeSimulations])

  // Motor difficulty: cursor delay
  useEffect(() => {
    if (!activeSimulations.has('motor_difficulty')) return

    const styleEl = document.createElement('style')
    styleEl.id = 'motor-difficulty-style'
    styleEl.textContent = `
      * { cursor: wait !important; }
      button, a, input, select, textarea {
        transition: all 0.8s ease-in-out !important;
      }
    `
    document.head.appendChild(styleEl)

    // Add delayed click handling
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'BUTTON' || target.tagName === 'A') {
        e.preventDefault()
        e.stopPropagation()
        setTimeout(() => {
          target.click()
        }, 500)
      }
    }

    // Use capture phase to intercept before regular handlers
    document.addEventListener('click', handleClick, { capture: true })

    return () => {
      styleEl.remove()
      document.removeEventListener('click', handleClick, { capture: true })
    }
  }, [activeSimulations])

  // Dyslexia simulation on main content
  useEffect(() => {
    if (isDyslexiaActive) {
      const main = document.querySelector('main')
      if (main) {
        startDyslexia(main as HTMLElement)
      }
    } else {
      stopDyslexia()
    }
  }, [isDyslexiaActive, startDyslexia, stopDyslexia])

  const hasActiveSimulations = activeSimulations.size > 0

  return (
    <section aria-labelledby="simulate-heading" className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 id="simulate-heading" className="text-xl font-semibold text-gray-900 dark:text-white">
            Ponte de Empatia
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Simule como seus alunos experienciam o conteúdo.
            Ative uma ou mais simulações para entender suas perspectivas.
          </p>
        </div>

        {hasActiveSimulations && (
          <button
            onClick={resetAll}
            className={cn(
              'rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white',
              'hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-red-600 transition-colors',
            )}
            aria-label="Desativar todas as simulações"
          >
            Resetar Tudo
          </button>
        )}
      </div>

      {/* Active simulation indicator */}
      <AnimatePresence>
        {hasActiveSimulations && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div
              role="status"
              aria-live="polite"
              className="flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
            >
              <span aria-hidden="true" className="text-lg">
                !
              </span>
              <span>
                {activeSimulations.size} simulação(ões) ativa(s).
                A página pode parecer diferente do normal.
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Simulation categories and toggles */}
      <div className="grid gap-6 sm:grid-cols-2">
        {SIMULATION_CATEGORIES.map((category) => {
          const categorySimulations = SIMULATIONS.filter(
            (s) => s.category === category.id,
          )
          return (
            <fieldset
              key={category.id}
              className="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
            >
              <legend className="px-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                {category.label}
              </legend>
              <div className="mt-2 flex flex-col gap-3">
                {categorySimulations.map((sim) => (
                  <SimulationToggle
                    key={sim.id}
                    simulation={sim}
                    isActive={activeSimulations.has(sim.id)}
                    onToggle={() => toggleSimulation(sim.id)}
                  />
                ))}
              </div>
            </fieldset>
          )
        })}
      </div>
    </section>
  )
}

/* --- Sub-component --- */

interface SimulationToggleProps {
  simulation: (typeof SIMULATIONS)[number]
  isActive: boolean
  onToggle: () => void
}

function SimulationToggle({ simulation, isActive, onToggle }: SimulationToggleProps) {
  return (
    <label
      className={cn(
        'flex cursor-pointer items-start gap-3 rounded-lg p-3 transition-colors',
        isActive
          ? 'bg-blue-50 dark:bg-blue-950'
          : 'hover:bg-gray-50 dark:hover:bg-gray-800',
      )}
    >
      <div className="relative mt-0.5 shrink-0">
        <input
          type="checkbox"
          role="switch"
          aria-checked={isActive}
          checked={isActive}
          onChange={onToggle}
          className="peer sr-only"
        />
        <div
          className={cn(
            'h-6 w-11 rounded-full transition-colors',
            isActive ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600',
          )}
          aria-hidden="true"
        />
        <div
          className={cn(
            'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform',
            isActive && 'translate-x-5',
          )}
          aria-hidden="true"
        />
      </div>
      <div className="flex flex-col">
        <span className="text-sm font-medium text-gray-900 dark:text-white">
          {simulation.label}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {simulation.description}
        </span>
      </div>
    </label>
  )
}
