// src/components/layout/bento-dashboard.tsx
import React from 'react'

// MEGA SPRINT 37: Bento Dashboard Skeleton
// Layout acessível baseado em Grid, responsivo e que escala via viewport fluidamente.
export const BentoDashboardLayout = ({
  children,
  header,
  sidebar,
}: {
  children: React.ReactNode
  header: React.ReactNode
  sidebar?: React.ReactNode
}) => {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row font-sans selection:bg-primary/20">
      
      {/* Master-Detail / Off-canvas Sidebar para Tablet e Desktop */}
      {sidebar && (
        <aside className="w-full md:w-72 border-r bg-card shadow-sm sticky top-0 md:h-screen hidden md:block z-20">
          {sidebar}
        </aside>
      )}

      <main className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden">
        {/* Global Header c/ Quiet Mode Toggle & A11y Controls */}
        <header className="sticky top-0 z-10 w-full backdrop-blur-md bg-background/80 border-b p-4 md:px-8 shadow-sm h-16 flex items-center">
          {header}
        </header>

        {/* Bento Grid Content Area */}
        <div className="flex-1 p-4 md:p-8 lg:p-12 w-full max-w-7xl mx-auto">
          {/*
            Grid definition: Responsive columns
            1 col mobile -> 2 cols tablet -> 3/4 cols large screens
          */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-[minmax(180px,auto)]">
            {children}
          </div>
        </div>
      </main>
      
      {/*
        F-MEGA-12: The Parking Lot (Mobile Sheet / Desktop Side Panel)
        This will overlay when called to clear working memory / ADHD distracting thoughts.
      */}
      <div id="a11y-parking-lot-portal" />
    </div>
  )
}